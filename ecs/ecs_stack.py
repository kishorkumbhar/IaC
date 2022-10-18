from aws_cdk import (
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_iam as iam,
    Stack,
)

from constructs import Construct

# stack = Stack(app, "ec2-service-with-task-networking")


class EcsStack(Stack):

    def __init__(self, scope: Construct, construct_id: str,vpc,**kwargs) -> None:
        super().__init__(scope, construct_id,**kwargs)
        
        #amazon managed policy Role
        ecs_role = iam.Role(self, "EcsRoleId",
                                    assumed_by=iam.ServicePrincipal(
                                        'ecs-tasks.amazonaws.com'),
                                    managed_policies=[
                                        iam.ManagedPolicy.from_aws_managed_policy_name(
                                            'AmazonS3ReadOnlyAccess'
                                        ),
                                        iam.ManagedPolicy.from_aws_managed_policy_name(
                                            'service-role/AmazonECSTaskExecutionRolePolicy'
                                        ),
                                        iam.ManagedPolicy.from_aws_managed_policy_name(
                                            'service-role/AmazonEC2ContainerServiceRole'
                                        )
                                    ]
                                )
        
        # Custom policy Non-Admin ecs
        # policy_document = {
        #                     "Version": "2012-10-17",
                            
                            
    
        #                     }
        
        # custom_policy_document = iam.PolicyDocument.from_json(policy_document)
        
        
        security_group = ec2.SecurityGroup(self,"cluster",vpc=vpc,security_group_name="Cluster-SG")
        security_group.add_ingress_rule(
                                        ec2.Peer.any_ipv4(),
                                        ec2.Port.tcp(80)
                                        )

        
        # Create a cluster
        cluster = ecs.Cluster(self, "FargateCluster", vpc=vpc)
        # Create a Task Definition for the container to start
        task_definition = ecs.FargateTaskDefinition(self, "FTD",
            memory_limit_mib=512,
            cpu=256,
            # compatibility=ecs.Compatibility.FARGATE,
            #network_mode="AwsVpc",
            execution_role=ecs_role,
            task_role=ecs_role,
        )

        task_definition.add_container("TheContainer",
            image=ecs.ContainerImage.from_registry("public.ecr.aws/nginx/nginx:1.22-alpine"),
            memory_limit_mib=256,
        )
        
        # cluster.enable_fargate_capacity_providers
        
        run_task= ecs.FargateService(self, "Service", 
                                     cluster=cluster,
                                     task_definition=task_definition,
                                     #vpc_subnets=subnets,
                                     assign_public_ip=True,
                                     security_groups=[security_group]
                                     )     
        
        
        # out=aws_cdk.CfnOutput(self,
        #                "customVpcOutput",
        #                value=,
        #                export_name="VpcId")