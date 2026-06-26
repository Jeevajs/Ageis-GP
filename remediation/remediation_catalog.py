REMEDIATION_ACTIONS = {
    "database": [
        {"action_id":"DB_POOL_INCREASE","title":"Increase DB connection pool temporarily","risk":"Medium","requires_approval":True,"command_preview":"Update DB_POOL_SIZE to approved temporary value","rollback":"Restore previous DB_POOL_SIZE"},
        {"action_id":"DB_KILL_STALE","title":"Kill stale database sessions","risk":"High","requires_approval":True,"command_preview":"Terminate stale DB sessions after review","rollback":"No direct rollback; monitor reconnection"}
    ],
    "memory": [
        {"action_id":"K8S_INCREASE_MEMORY","title":"Increase Kubernetes memory limit","risk":"Medium","requires_approval":True,"command_preview":"kubectl patch deployment <service> memory limit","rollback":"Revert deployment resource limit"},
        {"action_id":"CAPTURE_HEAP_DUMP","title":"Capture heap dump","risk":"Low","requires_approval":False,"command_preview":"Capture heap dump from affected pod","rollback":"Delete dump after analysis"}
    ],
    "consumer": [
        {"action_id":"SCALE_CONSUMER","title":"Scale consumer replicas","risk":"Medium","requires_approval":True,"command_preview":"kubectl scale deployment <consumer> --replicas=N","rollback":"Scale back to previous count"},
        {"action_id":"CHECK_PARTITIONS","title":"Check Kafka partition distribution","risk":"Low","requires_approval":False,"command_preview":"Describe consumer group and topic lag","rollback":"No rollback required"}
    ],
    "application": [
        {"action_id":"ROLLBACK_DEPLOYMENT","title":"Rollback recent deployment","risk":"High","requires_approval":True,"command_preview":"kubectl rollout undo deployment/<service>","rollback":"Roll forward after fix"},
        {"action_id":"VALIDATE_CONFIG","title":"Validate recent configuration changes","risk":"Low","requires_approval":False,"command_preview":"Compare current config with previous known-good","rollback":"No rollback required"}
    ],
    "network": [
        {"action_id":"CHECK_DEPENDENCY_HEALTH","title":"Check downstream dependency health","risk":"Low","requires_approval":False,"command_preview":"Query dependency health and latency metrics","rollback":"No rollback required"},
        {"action_id":"RESTART_UNHEALTHY_POD","title":"Restart unhealthy pod","risk":"Medium","requires_approval":True,"command_preview":"kubectl delete pod <pod-name>","rollback":"Kubernetes recreates pod; monitor readiness"}
    ],
    "hdfs": [
        {"action_id":"TRIGGER_HDFS_REREPLICATION","title":"Trigger HDFS block re-replication","risk":"Medium","requires_approval":True,"command_preview":"hdfs fsck and trigger replication repair","rollback":"No direct rollback; monitor NameNode"},
        {"action_id":"CHECK_DATANODE_HEALTH","title":"Check DataNode health","risk":"Low","requires_approval":False,"command_preview":"Check DataNode process, disk and network health","rollback":"No rollback required"}
    ]
}
DEFAULT_ACTIONS = [
    {"action_id":"COLLECT_DIAGNOSTICS","title":"Collect diagnostics","risk":"Low","requires_approval":False,"command_preview":"Collect logs, metrics, events and deployment metadata","rollback":"No rollback required"},
    {"action_id":"ESCALATE_OWNER","title":"Escalate to service owner","risk":"Low","requires_approval":False,"command_preview":"Notify owner with evidence and RCA report","rollback":"No rollback required"}
]
def get_actions_for_root_cause(root_cause):
    text = str(root_cause).lower()
    for key, actions in REMEDIATION_ACTIONS.items():
        if key in text:
            return actions
    return DEFAULT_ACTIONS
