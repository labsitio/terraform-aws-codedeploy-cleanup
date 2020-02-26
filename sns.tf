resource "aws_lambda_permission" "sns_notify_lambda" {
  statement_id  = "AllowExecutionFromSNS"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.codedeploy_cleanup.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = local.sns_topic_arn
}

data "aws_sns_topic" "this" {
  count = false == var.create_sns_topic ? 1 : 0
  name  = var.sns_topic_name
}

resource "aws_sns_topic" "this" {
  name = var.lambda_function_name
  tags = merge(var.tags, var.sns_topic_tags)
}

locals {
  sns_topic_arn = element(
    concat(
      aws_sns_topic.this.*.arn,
      data.aws_sns_topic.this.*.arn,
      [""],
    ),
    0,
  )
}

resource "aws_sns_topic_subscription" "sns_notify_lambda" {
  topic_arn = local.sns_topic_arn
  protocol  = "lambda"
  endpoint  = aws_lambda_function.codedeploy_cleanup.arn
}
