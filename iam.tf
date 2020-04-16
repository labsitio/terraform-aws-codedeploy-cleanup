resource "aws_iam_role" "lambda" {
  name_prefix        = "lambda"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
  tags               = merge(var.tags, var.iam_role_tags)
}

resource "aws_iam_role_policy" "lambda" {
  name_prefix = "lambda-policy-"
  role        = aws_iam_role.lambda.name
  policy      = data.aws_iam_policy_document.lambda.json
}

data "aws_iam_policy_document" "assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "lambda" {
  statement {
    sid    = "AllowDeleteAutoScalingGroupCodeDeploy"
    effect = "Allow"

    actions = [
      "autoscaling:DeleteAutoScalingGroup",
    ]

    resources = [
      "arn:aws:autoscaling:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:autoScalingGroup:*:autoScalingGroupName/CodeDeploy*",
    ]
  }
  statement {
    sid    = "AllowDescribeAutoScalingGroups"
    effect = "Allow"

    actions = [
      "autoscaling:DescribeAutoScalingGroups",
    ]

    resources = ["*"]
  }
  statement {
    sid    = "AllowGetDeployment"
    effect = "Allow"

    actions = [
      "codedeploy:GetDeployment",
    ]

    resources = ["*"]
  }
  statement {
    sid    = "AllowManagingEventRulesAndTargets"
    effect = "Allow"

    actions = [
      "events:DeleteRule",
      "events:RemoveTargets",
      "events:PutRule",
      "events:PutTargets",
    ]

    resources = [
      "arn:aws:events:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:rule/CodeDeployCleanup*"
    ]
  }
  statement {
    sid    = "AllowAddRemoveLambdaPermissionsToSelf"
    effect = "Allow"

    actions = [
      "lambda:AddPermission",
      "lambda:RemovePermission"
    ]

    resources = [
      "arn:aws:lambda:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:function:${var.lambda_function_name}"
    ]
  }
  statement {
    sid    = "AllowWriteToCloudwatchLogs"
    effect = "Allow"

    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]

    resources = [
      "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${var.lambda_function_name}:*:*",
      "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${var.lambda_function_name}:*",
    ]
  }
}
