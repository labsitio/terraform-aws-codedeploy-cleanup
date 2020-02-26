output "codedeploy_cleanup_topic_arn" {
  description = "The ARN of the SNS topic from which messages will be sent to Lambda"
  value       = local.sns_topic_arn
}

output "lambda_iam_role_arn" {
  description = "The ARN of the IAM role used by Lambda function"
  value       = aws_iam_role.lambda.arn
}

output "lambda_iam_role_name" {
  description = "The name of the IAM role used by Lambda function"
  value       = aws_iam_role.lambda.name
}

output "codedeploy_cleanup_lambda_function_arn" {
  description = "The ARN of the Lambda function"
  value       = aws_lambda_function.codedeploy_cleanup.arn
}

output "codedeploy_cleanup_lambda_function_name" {
  description = "The name of the Lambda function"
  value       = aws_lambda_function.codedeploy_cleanup.function_name
}

output "codedeploy_cleanup_lambda_function_last_modified" {
  description = "The date Lambda function was last modified"
  value       = aws_lambda_function.codedeploy_cleanup.last_modified
}

output "codedeploy_cleanup_lambda_function_version" {
  description = "Latest published version of your Lambda function"
  value       = aws_lambda_function.codedeploy_cleanup.version
}

output "lambda_cloudwatch_log_group_arn" {
  description = "The Amazon Resource Name (ARN) specifying the log group"
  value       = aws_cloudwatch_log_group.lambda.arn
}
