#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
COMPUTE_SLA_TEMPLATE = {
    "type": "compute",
    "templateId": "",
    "name": "dataAssetComputeExecutionAgreement",
    "description": "",
    "creator": "",
    "serviceAgreementTemplate": {
        "contractName": "EscrowComputeExecutionTemplate",
        "events": [
            {
                "name": "AgreementCreated",
                "actorType": "consumer",
                "handler": {
                    "moduleName": "EscrowComputeExecutionTemplate",
                    "functionName": "fulfillLockRewardCondition",
                    "version": "0.1",
                },
            }
        ],
        "fulfillmentOrder": [
            "lockReward.fulfill",
            "computeExecution.fulfill",
            "escrowReward.fulfill",
        ],
        "conditionDependency": {
            "lockReward": [],
            "computeExecution": [],
            "escrowReward": ["lockReward", "computeExecution"],
        },
        "conditions": [
            {
                "name": "lockReward",
                "timelock": 0,
                "timeout": 0,
                "contractName": "LockRewardCondition",
                "functionName": "fulfill",
                "parameters": [
                    {
                        "name": "_rewardAddress",
                        "type": "address",
                        "value": "{contract.EscrowReward.address}",
                    },
                    {
                        "name": "_amount",
                        "type": "uint256",
                        "value": "{parameter.price}",
                    },
                ],
                "events": [
                    {
                        "name": "Fulfilled",
                        "actorType": "publisher",
                        "handler": {
                            "moduleName": "lockRewardCondition",
                            "functionName": "fulfillComputeExecutionCondition",
                            "version": "0.1",
                        },
                    }
                ],
            },
            {
                "name": "computeExecution",
                "timelock": 0,
                "timeout": 0,
                "contractName": "ComputeExecutionCondition",
                "functionName": "fulfill",
                "parameters": [
                    {
                        "name": "_documentId",
                        "type": "bytes32",
                        "value": "{parameter.assetId}",
                    },
                    {"name": "_grantee", "type": "address", "value": ""},
                ],
                "events": [
                    {
                        "name": "Fulfilled",
                        "actorType": "publisher",
                        "handler": {
                            "moduleName": "accessSecretStore",
                            "functionName": "fulfillEscrowRewardCondition",
                            "version": "0.1",
                        },
                    },
                    {
                        "name": "TimedOut",
                        "actorType": "consumer",
                        "handler": {
                            "moduleName": "computeExecution",
                            "functionName": "fulfillEscrowRewardCondition",
                            "version": "0.1",
                        },
                    },
                ],
            },
            {
                "name": "escrowReward",
                "timelock": 0,
                "timeout": 0,
                "contractName": "EscrowReward",
                "functionName": "fulfill",
                "parameters": [
                    {
                        "name": "_amount",
                        "type": "uint256",
                        "value": "{parameter.price}",
                    },
                    {"name": "_receiver", "type": "address", "value": ""},
                    {"name": "_sender", "type": "address", "value": ""},
                    {
                        "name": "_lockCondition",
                        "type": "bytes32",
                        "value": "{contract.LockRewardCondition.address}",
                    },
                    {
                        "name": "_releaseCondition",
                        "type": "bytes32",
                        "value": "{contract.ComputeExecutionCondition.address}",
                    },
                ],
                "events": [
                    {
                        "name": "Fulfilled",
                        "actorType": "publisher",
                        "handler": {
                            "moduleName": "escrowRewardCondition",
                            "functionName": "verifyRewardTokens",
                            "version": "0.1",
                        },
                    }
                ],
            },
        ],
    },
}
