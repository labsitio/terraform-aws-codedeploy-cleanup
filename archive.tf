data "null_data_source" "lambda_file" {
  inputs = {
    filename = "${path.module}/functions/codedeploy_cleanup.py"
  }
}

data "null_data_source" "lambda_archive" {
  inputs = {
    filename = "${path.module}/functions/codedeploy_cleanup.zip"
  }
}

data "archive_file" "codedeploy_cleanup" {
  type        = "zip"
  source_file = data.null_data_source.lambda_file.outputs.filename
  output_path = data.null_data_source.lambda_archive.outputs.filename
}
