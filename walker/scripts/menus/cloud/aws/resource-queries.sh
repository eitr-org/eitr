#!/usr/bin/env bash

choose_distribution() {
  local distributions

  if ! distributions="$(aws_cli cloudfront list-distributions | jq -r '.DistributionList.Items[]? | "\(.DomainName)  \(.Id)"')"; then
    notify-send "CloudFront" "Failed to list distributions"
    return 1
  fi

  [ -z "$distributions" ] && notify-send "CloudFront" "No distributions found" && return 1
  printf "%s\n" "$distributions"
}

choose_log_group() {
  local log_groups

  if ! log_groups="$(aws_cli logs describe-log-groups | jq -r '.logGroups[].logGroupName')"; then
    notify-send "CloudWatch" "Failed to list log groups for $AWS_PROFILE"
    return 1
  fi

  if [ -z "$log_groups" ]; then
    notify-send "CloudWatch" "No log groups found for $AWS_PROFILE"
    return 1
  fi

  printf "%s\n" "$log_groups"
}

choose_user_pool() {
  local pools

  if ! pools="$(aws_cli cognito-idp list-user-pools --max-results 60 | jq -r '.UserPools[] | "\(.Name)  \(.Id)"')"; then
    notify-send "Cognito" "Failed to list user pools"
    return 1
  fi

  [ -z "$pools" ] && notify-send "Cognito" "No user pools found" && return 1
  printf "%s\n" "$pools"
}

choose_docdb_cluster() {
  local clusters

  if ! clusters="$(aws_cli docdb describe-db-clusters | jq -r '.DBClusters[].DBClusterIdentifier')"; then
    notify-send "DocumentDB" "Failed to list clusters"
    return 1
  fi

  [ -z "$clusters" ] && notify-send "DocumentDB" "No clusters found" && return 1
  printf "%s\n" "$clusters"
}

choose_ecr_repository() {
  local repositories

  if ! repositories="$(aws_cli ecr describe-repositories | jq -r '.repositories[].repositoryName')"; then
    notify-send "ECR" "Failed to list repositories for $AWS_PROFILE"
    return 1
  fi

  if [ -z "$repositories" ]; then
    notify-send "ECR" "No repositories found for $AWS_PROFILE"
    return 1
  fi

  printf "%s\n" "$repositories"
}

choose_ecs_cluster() {
  local clusters

  if ! clusters="$(aws_cli ecs list-clusters | jq -r '.clusterArns[] | split("/")[-1]')"; then
    notify-send "ECS" "Failed to list clusters for $AWS_PROFILE"
    return 1
  fi

  if [ -z "$clusters" ]; then
    notify-send "ECS" "No clusters found for $AWS_PROFILE"
    return 1
  fi

  printf "%s\n" "$clusters"
}

choose_ecs_service() {
  local cluster="$1"
  local services

  if ! services="$(aws_cli ecs list-services \
    --cluster "$cluster" \
    | jq -r '.serviceArns[] | split("/")[-1]')"; then
    notify-send "ECS" "Failed to list services in $cluster"
    return 1
  fi

  if [ -z "$services" ]; then
    notify-send "ECS" "No services found in $cluster"
    return 1
  fi

  printf "%s\n" "$services"
}

choose_workspace() {
  local workspaces

  if ! workspaces="$(aws_cli grafana list-workspaces | jq -r '.workspaces[] | "\(.name)  \(.id)"')"; then
    notify-send "Amazon Grafana" "Failed to list workspaces"
    return 1
  fi

  [ -z "$workspaces" ] && notify-send "Amazon Grafana" "No workspaces found" && return 1
  printf "%s\n" "$workspaces"
}

choose_iam_user() {
  local users

  if ! users="$(aws_cli iam list-users | jq -r '.Users[].UserName')"; then
    notify-send "IAM" "Failed to list users"
    return 1
  fi

  [ -z "$users" ] && notify-send "IAM" "No users found" && return 1
  printf "%s\n" "$users"
}

choose_lambda_function() {
  local functions

  if ! functions="$(aws_cli lambda list-functions | jq -r '.Functions[].FunctionName')"; then
    notify-send "Lambda" "Failed to list functions"
    return 1
  fi

  [ -z "$functions" ] && notify-send "Lambda" "No functions found" && return 1
  printf "%s\n" "$functions"
}

choose_db_instance() {
  local instances

  if ! instances="$(aws_cli rds describe-db-instances | jq -r '.DBInstances[].DBInstanceIdentifier')"; then
    notify-send "RDS" "Failed to list DB instances for $AWS_PROFILE"
    return 1
  fi

  if [ -z "$instances" ]; then
    notify-send "RDS" "No DB instances found for $AWS_PROFILE"
    return 1
  fi

  printf "%s\n" "$instances"
}

choose_db_cluster() {
  local clusters

  if ! clusters="$(aws_cli rds describe-db-clusters | jq -r '.DBClusters[].DBClusterIdentifier')"; then
    notify-send "RDS" "Failed to list DB clusters for $AWS_PROFILE"
    return 1
  fi

  if [ -z "$clusters" ]; then
    notify-send "RDS" "No DB clusters found for $AWS_PROFILE"
    return 1
  fi

  printf "%s\n" "$clusters"
}

choose_hosted_zone() {
  local zones

  if ! zones="$(aws_cli route53 list-hosted-zones | jq -r '.HostedZones[] | "\(.Name)  \(.Id | split("/")[-1])"')"; then
    notify-send "Route 53" "Failed to list hosted zones"
    return 1
  fi

  [ -z "$zones" ] && notify-send "Route 53" "No hosted zones found" && return 1
  printf "%s\n" "$zones"
}

choose_vpc() {
  local vpcs

  if ! vpcs="$(aws_cli ec2 describe-vpcs | jq -r '.Vpcs[] | "\((.Tags // [] | map(select(.Key == "Name"))[0].Value) // "<no-name>")  \(.VpcId)"')"; then
    notify-send "VPC" "Failed to list VPCs"
    return 1
  fi

  [ -z "$vpcs" ] && notify-send "VPC" "No VPCs found" && return 1
  printf "%s\n" "$vpcs"
}

choose_s3_bucket() {
  local buckets

  if ! buckets="$(aws_cli s3api list-buckets | jq -r '.Buckets[].Name')"; then
    notify-send "S3" "Failed to list buckets for $AWS_PROFILE"
    return 1
  fi

  if [ -z "$buckets" ]; then
    notify-send "S3" "No buckets found for $AWS_PROFILE"
    return 1
  fi

  printf "%s\n" "$buckets"
}
