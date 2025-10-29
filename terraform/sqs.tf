# SQS queue for video processing
resource "aws_sqs_queue" "video_processing" {
  name                       = local.sqs_queues.video_processing
  visibility_timeout_seconds = var.sqs_visibility_timeout
  message_retention_seconds  = var.sqs_message_retention
  max_message_size          = 262144 # 256 KB
  delay_seconds             = 0
  receive_wait_time_seconds = 10 # Enable long polling

  # Enable encryption
  sqs_managed_sse_enabled = true

  # Redrive policy for failed messages
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.video_processing_dlq.arn
    maxReceiveCount     = 3
  })

  tags = merge(
    local.common_tags,
    {
      Name        = local.sqs_queues.video_processing
      Description = "Queue for video processing tasks"
    }
  )
}

# Dead letter queue for failed processing
resource "aws_sqs_queue" "video_processing_dlq" {
  name                       = "${local.sqs_queues.video_processing}-dlq"
  message_retention_seconds  = 1209600 # 14 days
  sqs_managed_sse_enabled   = true

  tags = merge(
    local.common_tags,
    {
      Name        = "${local.sqs_queues.video_processing}-dlq"
      Description = "Dead letter queue for failed video processing"
    }
  )
}

# CloudWatch alarm for DLQ messages
resource "aws_cloudwatch_metric_alarm" "video_processing_dlq_alarm" {
  alarm_name          = "${local.name_prefix}-video-processing-dlq"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Average"
  threshold           = 0
  alarm_description   = "Alert when messages appear in the DLQ"
  treat_missing_data  = "notBreaching"

  dimensions = {
    QueueName = aws_sqs_queue.video_processing_dlq.name
  }

  tags = local.common_tags
}

# SQS queue policy for Lambda access
resource "aws_sqs_queue_policy" "video_processing" {
  queue_url = aws_sqs_queue.video_processing.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowLambdaSend"
        Effect = "Allow"
        Principal = {
          AWS = aws_iam_role.lambda_execution.arn
        }
        Action = [
          "sqs:SendMessage",
          "sqs:GetQueueUrl"
        ]
        Resource = aws_sqs_queue.video_processing.arn
      },
      {
        Sid    = "AllowLambdaReceive"
        Effect = "Allow"
        Principal = {
          AWS = aws_iam_role.lambda_execution.arn
        }
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
          "sqs:ChangeMessageVisibility"
        ]
        Resource = aws_sqs_queue.video_processing.arn
      }
    ]
  })
}
