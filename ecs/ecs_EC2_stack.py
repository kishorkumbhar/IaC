from operator import mod
from aws_cdk import (
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_iam as iam,
    aws_autoscaling as autoscaling,
    aws_elasticloadbalancingv2 as elb,
    Stack,
)
import aws_cdk as cdk
from constructs import Construct

# add dependencies


class EcsEC2Stack(Stack):

    def __init__(self, scope: Construct, construct_id: str,vpc,**kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Read BootStrap Script:
        try:
            with open("/home/cwm/ecs/user_data.sh", mode="r") as file:
                user_data = file.read()
        except OSError:
            print('Unable to read UserData script')
        
        
        #amazon managed policy Role
        ecs_EC2_role = iam.Role(self, "EcsEc2RoleId",
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
                                        ),
                                        iam.ManagedPolicy.from_aws_managed_policy_name(
                                            'AWSOpsWorksCloudWatchLogs'
                                        ),
                                        iam.ManagedPolicy.from_aws_managed_policy_name(
                                            'AmazonSSMManagedInstanceCore'
                                        )
                                    ]
                                )
        
        # Create a security group that allows HTTP traffic on port 80 for our containers without modifying the security group on the instance
        security_group = ec2.SecurityGroup(self, "Ecs-EC2",
                                           vpc=vpc,
                                           allow_all_outbound=False,
                                           security_group_name="ECS-EC2-SG"
                                           )
        security_group.add_ingress_rule(ec2.Peer.any_ipv4(),
                                        ec2.Port.tcp(80)
                                        )
        
        # Cluster Creation
        cluster = ecs.Cluster(self, "ecs-EC2-cluster",vpc=vpc,cluster_name="ECS-EC2-Cluster", container_insights=True)
        
        # Either add default capacity
        cluster.add_capacity("DefaultAutoScalingGroupCapacity",
                            instance_type=ec2.InstanceType("t3a.medium"),
                            desired_capacity=2,
                            key_name="cwm-pvt"
                            )
        
        # asg = autoscaling.AutoScalingGroup(self, "Ecs-EC2-AutoScalingGroup",
        #                                    vpc=vpc,
        #                                    vpc_subnets=ec2.SubnetSelection(#availability_zones=["ap-south-1a"],
        #                                                                    subnet_type=ec2.SubnetType.PUBLIC
        #                                                                    ),
        #                                    instance_type=ec2.InstanceType(instance_type_identifier="t3a.medium"),
        #                                    machine_image=ecs.EcsOptimizedImage.amazon_linux2(),
        #                                    security_group=security_group,
        #                                    user_data=ec2.UserData.custom(user_data),
        #                                    )

        # capacity_provider = ecs.AsgCapacityProvider(self, "Ecs-EC2-AsgCapacityProvider",
        #                                             auto_scaling_group=asg)
        # cluster.add_asg_capacity_provider(capacity_provider)

        
        # Task definition with its own elastic network interface
        task_definition = ecs.Ec2TaskDefinition(self, "Ecs-EC2-Nginx-TD",
                                                network_mode=ecs.NetworkMode.BRIDGE,
                                                execution_role=ecs_EC2_role,
                                                task_role=ecs_EC2_role
                                                )
        
        # Adding Caintainers to task defination 
        web_container = task_definition.add_container("Ecs-EC2-nginx",
                                                      image=ecs.ContainerImage.from_registry("public.ecr.aws/nginx/nginx:1.22-alpine"),                                                      
                                                      memory_reservation_mib=256,
                                                      essential=True,
                                                      logging=ecs.LogDrivers.aws_logs(stream_prefix="ECS",
                                                                                      )
                                                      )
        # Port mapping
        port_mapping = ecs.PortMapping(container_port=80,
                                       protocol=ecs.Protocol.TCP,
                                       host_port=0
                                       )
        web_container.add_port_mappings(port_mapping)


        # Create the service
        Ec2_service = ecs.Ec2Service(self, "ecs-EC2-service",
                                 cluster=cluster,
                                 task_definition=task_definition,
                                 #security_groups=[security_group],
                                 service_name="Ecs-Ec2-Service",
                                 desired_count=1
                                 )
        
        # Setup Autoscaling Policy
        scaling=Ec2_service.auto_scale_task_count(max_capacity=4,
                                                min_capacity=2
                                                )
        scaling.scale_on_cpu_utilization("CpuScaling",
                                        target_utilization_percent=50,
                                        scale_in_cooldown=cdk.Duration.seconds(60),
                                        scale_out_cooldown=cdk.Duration.seconds(60)
                                        )
        # Integrating capacity wiith cluster
        
        
        # Create ALB
        lb = elb.ApplicationLoadBalancer(
                                        self, "LB",
                                        vpc=vpc,
                                        internet_facing=True,
                                        vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
                                            #availability_zones=["ap-south-1a","ap-south-1b"],one_per_az=True),
                                        load_balancer_name="ECS-EC2-LB"
                                        )
        
        # Tagging
        # cdk.Tags.of(lb).add("Name", "ECS-EC2-LB")
        
        # Add listener
        listener = lb.add_listener("PublicListener",
                                    port=80,
                                    open=True
                                    )
        
        # Allowing incomiing traffic to alb
        #asg.connections.allow_from(lb, port_range=ec2.Port.tcp_range(32768, 65535), description="allow incoming traffic from ALB")

        # Health Check
        health_check = elb.HealthCheck(
                                    interval= cdk.Duration.seconds(60),
                                    path="/health",
                                    timeout= cdk.Duration.seconds(5)
                                    )

        # Attach ALB to ECS Service
        listener.add_targets("ECS",
                            port=80,
                            targets=[Ec2_service],
                            health_check=health_check,
                            target_group_name="EcsEC2-TG"
                            )

        # Cfn output
        cdk.CfnOutput(self,"LBDNS",
                      value=lb.load_balancer_dns_name,
                      export_name="LB-DNS")