# AWS CodeDeploy Cleanup Terraform module
This module creates an SNS topic (or uses an existing one) and a Lambda function that cleans up Auto Scaling Groups that are the result of failed Blue/Green deployments using CodeDeploy after a provided time period. The issue is described best on the AWS forums [here](https://forums.aws.amazon.com/thread.jspa?threadID=265522).

> :warning: The code in this module will *delete* Auto Scaling Groups. We've done our best to do sanity checking before deleting but we recommend you test this carefully in a non production environment first to ensure you understand how it works.
>
## Usage

```hcl
module "codedeploy_cleanup" {
 source = "git@github.com:anchor/terraform-aws-codedeploy-cleanup.git?ref=v1.0.0"
 lambda_function_name = "CodeDeployCleanup"
 sns_topic_name = "CodeDeployCleanup"
 keep_alive = 60
}
```

Once you've created the resources with this module you'll need to configure CodeDeploy to send failure events for your deployments to the created SNS topic.

<!-- BEGINNING OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
## Providers

| Name | Version |
|------|---------|
| archive | n/a |
| aws | n/a |
| null | n/a |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:-----:|
| cloudwatch\_log\_group\_kms\_key\_id | The ARN of the KMS Key to use when encrypting log data for Lambda | `string` | n/a | yes |
| cloudwatch\_log\_group\_retention\_in\_days | Specifies the number of days you want to retain log events in log group for Lambda. | `number` | `0` | no |
| cloudwatch\_log\_group\_tags | Additional tags for the Cloudwatch log group | `map(string)` | `{}` | no |
| create\_sns\_topic | Whether to create new SNS topic | `bool` | `true` | no |
| iam\_role\_tags | Additional tags for the IAM role | `map(string)` | `{}` | no |
| keep\_alive | How many minutes after being a failed deploy should we wait before removing the Auto Scaling Group | `number` | n/a | yes |
| lambda\_function\_description | Description to use for the Lambda function | `string` | `"Cleans up Auto Scaling Groups left over from failed CodeDeploy Deployments"` | no |
| lambda\_function\_name | Name to use for the Lambda function | `string` | n/a | yes |
| lambda\_function\_tags | Additional tags for the Lambda function | `map(string)` | `{}` | no |
| reserved\_concurrent\_executions | The amount of reserved concurrent executions for this lambda function. A value of 0 disables lambda from being triggered and -1 removes any concurrency limitations | `number` | `-1` | no |
| sns\_topic\_name | The name of the SNS topic to create | `string` | n/a | yes |
| sns\_topic\_tags | Additional tags for the SNS topic | `map(string)` | `{}` | no |
| tags | A map of tags to add to resources | `map(string)` | `{}` | no |

## Outputs

| Name | Description |
|------|-------------|
| codedeploy\_cleanup\_lambda\_function\_arn | The ARN of the Lambda function |
| codedeploy\_cleanup\_lambda\_function\_last\_modified | The date Lambda function was last modified |
| codedeploy\_cleanup\_lambda\_function\_name | The name of the Lambda function |
| codedeploy\_cleanup\_lambda\_function\_version | Latest published version of your Lambda function |
| codedeploy\_cleanup\_topic\_arn | The ARN of the SNS topic from which messages will be sent to Lambda |
| lambda\_cloudwatch\_log\_group\_arn | The Amazon Resource Name (ARN) specifying the log group |
| lambda\_iam\_role\_arn | The ARN of the IAM role used by Lambda function |
| lambda\_iam\_role\_name | The name of the IAM role used by Lambda function |

<!-- END OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
