variable "create_sns_topic" {
  description = "Whether to create new SNS topic"
  type        = bool
  default     = true
}

variable "cloudwatch_log_group_retention_in_days" {
  description = "Specifies the number of days you want to retain log events in log group for Lambda."
  type        = number
  default     = 0
}

variable "cloudwatch_log_group_kms_key_id" {
  description = "The ARN of the KMS Key to use when encrypting log data for Lambda"
  type        = string
  default     = null
}

variable "keep_alive" {
  description = "How many minutes after being a failed deploy should we wait before removing the Auto Scaling Group"
  type        = number
}

variable "lambda_function_name" {
  description = "Name to use for the Lambda function"
  type        = string
}

variable "lambda_function_description" {
  description = "Description to use for the Lambda function"
  type        = string
  default     = "Cleans up Auto Scaling Groups left over from failed CodeDeploy Deployments"
}

variable "reserved_concurrent_executions" {
  description = "The amount of reserved concurrent executions for this lambda function. A value of 0 disables lambda from being triggered and -1 removes any concurrency limitations"
  type        = number
  default     = -1
}

variable "sns_topic_name" {
  description = "The name of the SNS topic to create"
  type        = string
}

variable "tags" {
  description = "A map of tags to add to resources"
  type        = map(string)
  default     = {}
}

variable "iam_role_tags" {
  description = "Additional tags for the IAM role"
  type        = map(string)
  default     = {}
}

variable "lambda_function_tags" {
  description = "Additional tags for the Lambda function"
  type        = map(string)
  default     = {}
}

variable "sns_topic_tags" {
  description = "Additional tags for the SNS topic"
  type        = map(string)
  default     = {}
}

variable "cloudwatch_log_group_tags" {
  description = "Additional tags for the Cloudwatch log group"
  type        = map(string)
  default     = {}
}
