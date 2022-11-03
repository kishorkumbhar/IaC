from constructs import Construct
from aws_cdk import (
    Stage
)
from ecs.ecs_EC2_stack import EcsEC2Stack

class EcsPipelineStage(Stage):

    def __init__(self, scope: Construct, id: str,vpc, **kwargs):
        super().__init__(scope, id, **kwargs)
    
        service=EcsEC2Stack(self,'EcsService',vpc=vpc)
    