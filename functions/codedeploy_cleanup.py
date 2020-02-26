"""
CodeDeployCleanup
Author: Andrew Jeffree (andrew.jeffree@anchor.com.au)
Last Updated: 24/02/2020
Triggered via messages sent to a SNS topic from CodeDeploy on a failed deployment.
Schedules a cleanup via CloudWatch Events to invoke this function at a later time,
to remove the left over Auto Scaling Group which isn't used.

Fixes issue described at https://forums.aws.amazon.com/thread.jspa?threadID=265522
"""
import json
import logging
import os
import sys
from datetime import datetime
from datetime import timedelta

import boto3
import pytz

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)


def lambda_handler(event, context):
    lambda_arn = context.invoked_function_arn
    action = event.get('action', 'sns')
    if action == 'cleanup':
        deployment_id = event.get('deploymentId')
        deployment_group = event.get('deploymentGroup')
        remove_cloudwatch_rule(deployment_group, deployment_id)
        remove_lambda_permission(lambda_arn, deployment_group, deployment_id)
        remove_auto_scaling_group(deployment_group, deployment_id)

    else:
        message = json.loads(event['Records'][0]['Sns']['Message'])
        deployment_id = message.get('deploymentId')
        deployment_group = message.get('deploymentGroupName')
        deployment_status = message.get('status')

        # Just for sanity purposes check to make sure we're only actioning failed
        # deployments. As someone could change the configuration in CodeDeploy to
        # send all events to us and then we'd remove a working AutoScaling group.
        if deployment_status != 'FAILED':
            LOGGER.warning("Deployment Status isn't 'FAILED'. Nothing to do.")
            sys.exit()

        asg_exists = check_auto_scaling_group(deployment_group, deployment_id)
        if not asg_exists:
            sys.exit()
        # KEEP_AlIVE is how long in *minutes* we should keep a failed environment for.
        keep_alive = int(os.environ.get('KEEP_ALIVE'))

        cw_rule, cw_rule_arn = create_cloudwatch_rule(deployment_group, deployment_id, keep_alive)
        put_cloudwatch_target(deployment_group, deployment_id, lambda_arn, cw_rule)
        add_lambda_permission(cw_rule_arn, lambda_arn, deployment_group, deployment_id)


def check_auto_scaling_group(deployment_group, deployment_id):
    """
    Checks if an Auto Scaling Group actually exists with the name
    that's generated based on the provided parameters.

    :type deployment_group: str
    :type deployment_id: str
    :param deployment_group: CodeDeploy Deployment Group Name
    :param deployment_id: CodeDeploy Deployment Id
    :return: Boolean resulting from check
    :rtype: bool
    """
    client = boto3.client('autoscaling')
    name = f"CodeDeploy_{deployment_group}_{deployment_id}"
    LOGGER.info(f"Checking to see if there is an Auto Scaling Group called {name}")
    response = client.describe_auto_scaling_groups(
        AutoScalingGroupNames=[
            name,
        ]
    )
    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        raise Exception(f'ERROR {response}')
    elif response['AutoScalingGroups']:
        LOGGER.info(f'Success found Auto Scaling Group called {name}')
        return True
    else:
        LOGGER.error(f'No Auto Scaling Group called {name} exists')
        return False


def remove_auto_scaling_group(deployment_group, deployment_id):
    """
    Remove the Auto Scaling that is left over the from failed deployment.
    We do check to make sure that it's not somehow in use before deletion.
    :type deployment_group: str
    :type deployment_id: str
    :param deployment_group: CodeDeploy Deployment Group Name
    :param deployment_id: CodeDeploy Deployment Id
    :return
    """
    name = f"CodeDeploy_{deployment_group}_{deployment_id}"
    LOGGER.info(f'Preparing to delete Auto Scaling Group called {name}')
    LOGGER.info(f'Checking if {name} is associated with a load balancer')
    client = boto3.client('autoscaling')
    response = client.describe_auto_scaling_groups(
        AutoScalingGroupNames=[
            name,
        ]
    )
    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        raise Exception(f'ERROR {response}')
    if response['AutoScalingGroups'][0]['TargetGroupARNs'] or \
            response['AutoScalingGroups'][0]['LoadBalancerNames']:
        raise Exception(f'ERROR Auto Scaling Group {name} attached to Load Balancer')

    LOGGER.info(f'Good to proceed. Deleting Auto Scaling Group {name}')
    # We use ForceDelete as it'll clean the instances up, whereas
    # otherwise we need to do a lot more work to cleanup instances
    # then delete the auto scaling group.
    response = client.delete_auto_scaling_group(
        AutoScalingGroupName=name,
        ForceDelete=True,
    )
    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        raise Exception(f'ERROR {response}')
    LOGGER.info(f'Auto Scaling Group {name} has been deleted')


def remove_cloudwatch_rule(deployment_group, deployment_id):
    """
    Remove the CloudWatch rule that triggered this lambda and its targets
    :type deployment_group: str
    :type deployment_id: str
    :param deployment_group: CodeDeploy Deployment Group Name
    :param deployment_id: CodeDeploy Deployment Id
    :return
    """
    client = boto3.client('events')
    rule_name = f'CodeDeployCleanup_{deployment_group}_{deployment_id}'
    LOGGER.info(f'Preparing to delete CloudWatch rule {rule_name}')
    # We need to remove all targets on a rule before we can remove it.
    # Thankfully we already know what the target on the rule is called.
    LOGGER.info(f'Removing targets on {rule_name}')
    response = client.remove_targets(
        Rule=rule_name,
        Ids=[
            'CodeDeployCleanupLambda'
        ]
    )
    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        raise Exception(f'ERROR {response}')
    LOGGER.info(f'Removed targets on {rule_name}')
    LOGGER.info(f'Deleting CloudWatch rule {rule_name}')
    response = client.delete_rule(
        Name=rule_name,
    )
    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        raise Exception(f'ERROR {response}')
    LOGGER.info(f'CloudWatch rule {rule_name} has been deleted')


def create_cloudwatch_rule(deployment_group, deployment_id, minutes):
    """
    Create a CloudWatch rule that will trigger at the appropriate time to call
    this lambda function again with the action of cleanup.
    :type deployment_group: str
    :type deployment_id: str
    :type minutes: int
    :param deployment_group: CodeDeploy Deployment Group Name
    :param deployment_id: CodeDeploy Deployment Id
    :param minutes: number of minutes
    :return: rule_name and rule_arn
    :rtype: str, str
    """
    client = boto3.client('events')
    cron = generate_cron(minutes)
    rule_name = f"CodeDeployCleanup_{deployment_group}_{deployment_id}"
    LOGGER.info(f'Creating CloudWatch rule')
    response = client.put_rule(
        Name=rule_name,
        ScheduleExpression=cron,
        State='ENABLED',
        Description=f"CodeDeployCleanup of failed deployment: {deployment_id} in {deployment_group}"
    )
    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        raise Exception(f'ERROR {response}')
    LOGGER.info(f'Successfully created CloudWatch rule {rule_name}')
    rule_arn = response['RuleArn']
    return rule_name, rule_arn


def put_cloudwatch_target(deployment_group, deployment_id, lambda_arn, rule_name):
    """
    Create a CloudWatch target to call this Lambda function and associate it
    with the provided CloudWatch rule.
    :type deployment_group: str
    :type deployment_id: str
    :type lambda_arn: str
    :type rule_name: str
    :param deployment_group: CodeDeploy Deployment Group Name
    :param deployment_id: CodeDeploy Deployment Id
    :param lambda_arn: ARN of *this* lambda function to use as a target
    :param rule_name: Name of the rule to attach the target to
    :return
    """
    LOGGER.info(f'Putting target for Lambda on {rule_name}')
    client = boto3.client('events')
    target_input_json = {
        'action': 'cleanup',
        'deploymentId': deployment_id,
        'deploymentGroup': deployment_group,
    }
    response = client.put_targets(
        Rule=rule_name,
        Targets=[
            {
                'Id': 'CodeDeployCleanupLambda',
                'Arn': lambda_arn,
                'Input': json.dumps(target_input_json),
            }
        ]
    )
    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        raise Exception(f'ERROR {response}')
    LOGGER.info(f'Successfully put target for Lambda on {rule_name}')


def add_lambda_permission(cw_arn, lambda_arn, deployment_group, deployment_id):
    """
    Add permissions for the provided CloudWatch Rule to invoke the function.
    :type cw_arn: str
    :type lambda_arn: str
    :type deployment_id: int
    :param cw_arn: ARN of the CloudWatch Rule
    :param lambda_arn: ARN of *this* Lambda function
    :param deployment_id: CodeDeploy Deployment Id used for unique StatementId
    :return:
    """
    LOGGER.info('Granting CloudWatch permissions to invoke this Lambda function')
    client = boto3.client('lambda')
    response = client.add_permission(
        FunctionName=lambda_arn,
        StatementId=f"CodeDeployCleanup-{deployment_group}-{deployment_id}",
        Action="lambda:InvokeFunction",
        Principal="events.amazonaws.com",
        SourceArn=cw_arn
    )
    if response['ResponseMetadata']['HTTPStatusCode'] != 201:
        raise Exception(f'ERROR {response}')
    LOGGER.info('Successfully granted permissions')


def remove_lambda_permission(arn, deployment_group, deployment_id):
    """
    Remove previously provided permissions for the now removed CloudWatch Rule
    to invoke this function.
    :type arn: str
    :type deployment_id: str
    :param arn: ARN of *this* Lambda function
    :param deployment_id: CodeDeploy Deployment Id used for unique StatementId
    :return:
    """
    LOGGER.info('Removing permissions for removed CloudWatch rule to invoke this Lambda Function')
    client = boto3.client('lambda')
    response = client.remove_permission(
        FunctionName=arn,
        StatementId=f"CodeDeployCleanup-{deployment_group}-{deployment_id}"
    )
    if response['ResponseMetadata']['HTTPStatusCode'] != 204:
        raise Exception(f'ERROR {response}')
    LOGGER.info('Successfully removed permissions')


def generate_cron(minutes):
    """
    Generate the appropriate cron syntax as a string in UTC for CloudWatch

    :type minutes: int
    :param minutes: number of minutes
    :return: generated cron string
    :rtype: str
    """
    # Since we just take x minutes we need to convert that to hours *and* minutes
    # so we can use timedelta to get the future time.
    hours = minutes // 60
    actual_minutes = minutes % 60
    timezone = pytz.timezone('UTC')
    now = timezone.localize(datetime.utcnow())
    cron_time = now + timedelta(minutes=actual_minutes, hours=hours)
    # CloudWatch cron has 6 fields not 5. They added a year field at the end.
    cron = f'cron({cron_time:%M} {cron_time:%H} {cron_time:%d} {cron_time:%m} ? *)'
    return cron
