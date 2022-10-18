#!/usr/bin/env python3
import os

import aws_cdk as cdk

from ecs.vpc_stack import VpcStack
from ecs.ecs_stack import EcsStack
from ecs.ecs_EC2_stack import EcsEC2Stack

app = cdk.App()
vpc=VpcStack(app,"VPC")
EcsStack(app, "EcsStack",vpc=vpc.customvpc)
EcsEC2Stack(app,"ECS-EC2-Stack",vpc=vpc.customvpc)



app.synth()
