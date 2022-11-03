from aws_cdk import (
    aws_codecommit as codecommit,
    aws_codebuild as codeuild,
    aws_codepipeline as codepipeline,
       
    Stack,
)

from constructs import Construct

class Pipeline_ECS_EC2_Stack(Stack):
    
    def __init__(self, scope: Construct, construct_id: str,**kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        repo=codecommit.Repository(
            self, 
            'ECS-EC2-CICD',
            repository_name= "ECS-EC2-CICD"
            )
        
        pipeline = codepipeline.Pipeline(
            self,
            "ECS-EC2-Pipeline",
            synth=codepipeline.ShellStep(
                "Synth",
                input=codepipeline.CodePipelineSource.code_commit(repo, "master"),
                commands=[
                    "",  # Installs the cdk cli on Codebuild
                    "",  # Instructs Codebuild to install required packages
                    ""
                ]
            )
        )