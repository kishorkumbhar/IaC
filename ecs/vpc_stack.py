from aws_cdk import (
    aws_ec2 as ec2,
    Stack,
)

from constructs import Construct

class VpcStack(Stack):

    @property
    def customvpc(self):
        return self.vpc
    
    # @property
    # def subnet_type(self):
    #     return self.public_subnets
    
    def __init__(self, scope: Construct, construct_id: str,**kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
    
        self.vpc = ec2.Vpc(self, "Vpc",
            cidr="10.0.0.0/16",
            max_azs=2,
            nat_gateways=1,
            subnet_configuration=[
            ec2.SubnetConfiguration(
                name="public",cidr_mask=24, subnet_type=ec2.SubnetType.PUBLIC,#tags="public-1-a"
                ),
            ec2.SubnetConfiguration(
                name="private_with_NAT", cidr_mask=24, subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT,#tags="public-1-b"
                ),
            ec2.SubnetConfiguration(
                name="private", cidr_mask=24, subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,#tags="public-1-c"
                ),
            ]
        )
        
        # Filter out subnets
        private_subnets = self.vpc.select_subnets(
             subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,#availability_zones=[
            #     "ap-south-1"]
        )
        #print(private_subnets.subnet_ids)
        private_NAT= self.vpc.select_subnets(
             subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT,#availability_zones=[
            #     "ap-south-1b"]
        )
        #print(private_NAT.subnet_ids)
        self.public_subnets = self.vpc.select_subnets(
            subnet_type=ec2.SubnetType.PUBLIC,#availability_zones=[
            #    "ap-south-1c"]
        )