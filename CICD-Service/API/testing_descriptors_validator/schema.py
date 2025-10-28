VALIDATION_SCHEMA = {
    'test_info': {
        'required': True,
        'type': 'dict',
        'schema': {
            'netapp_id': {
                'required': True,
                'type': 'string'
            },
            'network_service_id': {
                'required': True,
                'type': 'string'
            },
            'testbed_id': {
                'required': True,
                'type': 'string'
            },
            'description': {
                'required': False,
                'type': 'string'
            }
        }
    },
'metrics_collection': {
        'required': False,
        'type': 'list',
        'schema': {
            'type': 'dict',
            'schema': {
                'job_name': {'required': True, 'type': 'string'},
                'metrics_collection': {
                    'required': True,
                    'type': 'list',
                    'schema': {
                        'type': 'dict',
                        'schema': {
                            'type': {'required': True, 'type': 'string'},
                            'collection_endpoint': {'required': True, 'type': 'string'}
                        }
                    }
                },
                'viewer': {
                    'required': False,
                    'type': 'dict',
                    'schema': {
                        'type': {'required': True, 'type': 'string'},
                        'dashboard_src': {'required': False, 'type': 'string'},
                        'name_for_dashboard': {'required': False, 'type': 'string'}
                    }
                }
            }
        }
    },

    # New top-level log_collection
    'log_collection': {
        'required': False,
        'type': 'list',
        'schema': {
            'type': 'dict',
            'schema': {
                'test_agent_name': {'required': True, 'type': 'string'},
                'type': {'required': True, 'type': 'string'},
                'viewer': {
                    'required': False,
                    'type': 'string'  # or dict if you expect more fields later
                }
            }
        }
    },
    'test_phases': {
        'required': True,
        'type': 'dict',
        'schema': {
            'setup': {
                'required': True,
                'type': 'dict',
                'schema': {
                    'deployments': {
                        'required': True,
                        'type': 'list',
                        'schema': {
                            'type': 'dict',
                            'schema': {
                                'deployment_id': {
                                    'required': True,
                                    'type': 'integer'
                                },
                                'name': {
                                    'required': True,
                                    'type': 'string'
                                },
                                'descriptor': {
                                    'required': True,
                                    'type': 'string'
                                },
                                'id': {
                                    'required': True,
                                    'type': 'string'
                                },
                                'parameters': {
                                    'required': False,
                                    'type': 'list',
                                    'schema': {
                                        'type': 'dict',
                                        'schema': {
                                            'key': {
                                                'required': True,
                                                'type': 'string'
                                            },
                                            'value': {
                                                'required': True,
                                            },
                                        },
                                    },
                                }
                            },
                        },
                    },
                    'testcases': {
                        'required': True,
                        'type': 'list',
                        'schema': {
                            'type': 'dict',
                            'schema': {
                                'testcase_id': {
                                    'required': True,
                                    'type': 'integer'
                                },
                                'name': {
                                    'required': True,
                                    'type': 'string'
                                },
                                'description': {
                                    'required': False,
                                    'type': 'string'
                                },
                                'type': {
                                    'required': True,
                                    'type': 'string'
                                },
                                'scope': {
                                    'required': True,
                                    'type': 'string'
                                },
                                'name': {
                                    'required': True,
                                    'type': 'string'
                                },
                                'parameters': {
                                    'required': False,
                                    'type': 'list',
                                    'schema': {
                                        'type': 'dict',
                                        'schema': {
                                            'key': {
                                                'required': True,
                                                'type': 'string'
                                            },
                                            'value': {
                                                'required': True,
                                            },
                                        },
                                    },
                                },
                            },
                        },
                    },
                    'metrics_collection': {
                        'required': False,
                        'type': 'list',
                        'schema': {
                            'type': 'dict',
                            'schema': {
                                'metrics_collection_id': {
                                    'required': True,
                                    'type': 'integer'
                                },
                                'description': {
                                    'required': False,
                                    'type': 'string'
                                },
                                'parameters': {
                                    'required': True,
                                    'type': 'list',
                                    'schema': {
                                        'type': 'dict',
                                        'schema': {
                                            'key': {
                                                'required': True,
                                                'type': 'string'
                                            },
                                            'value': {
                                                'required': True,
                                            },
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
            },
            'execution': {
                'required': True,
                'type': 'list',
                'schema': {
                    'type': 'dict',
                    'required': True,
                    'schema': {
                        'batch_id': {
                            'required': True,
                            'type': 'integer'
                        },
                        'scope': {
                            'required': True,
                            'type': 'string'
                        },
                        'executions': {
                            'required': True,
                            'type': 'list',
                            'schema': {
                                'type': 'dict',
                                'schema': {
                                    'execution_id': {
                                        'required': True,
                                        'type': 'integer'
                                    },
                                    'name': {
                                        'required': False,
                                        'type': 'string'
                                    },
                                    'testcase_ids': {
                                        'required': False,
                                        'type': 'list',
                                        'schema': {
                                            'type': 'integer',
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
            },
        },
    },
}