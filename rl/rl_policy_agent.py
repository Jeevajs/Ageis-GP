class RLRemediationPolicyAgent:
    """
    RL-style remediation policy module.
    Current version is a safe policy baseline.
    It can later be replaced with PPO/DQN trained model.
    """

    def extract_state(self, incident, root_cause):
        text = (
            f"{incident.get('alert','')} "
            f"{incident.get('logs','')} "
            f"{incident.get('metrics','')} "
            f"{root_cause}"
        ).lower()

        return {
            "is_memory": int("memory" in text or "oom" in text),
            "is_kafka": int("kafka" in text or "consumer lag" in text),
            "is_db": int("database" in text or "connection pool" in text or "jdbc" in text),
            "is_deploy": int("deployment" in text or "http 500" in text or "nullpointer" in text),
            "is_network": int("network" in text or "timeout" in text or "packet loss" in text),
            "severity": incident.get("severity", "P2"),
        }

    def recommend_action(self, incident, root_cause):
        state = self.extract_state(incident, root_cause)

        if state["is_kafka"]:
            action = "scale_service"
            reward = 9.0
        elif state["is_memory"]:
            action = "increase_memory"
            reward = 8.5
        elif state["is_db"]:
            action = "increase_db_pool"
            reward = 8.8
        elif state["is_deploy"]:
            action = "rollback_deployment"
            reward = 9.2
        elif state["is_network"]:
            action = "route_traffic_alternate_path"
            reward = 7.5
        else:
            action = "restart_service"
            reward = 6.0

        return {
            "agent": "RLRemediationPolicyAgent",
            "state": state,
            "recommended_action": action,
            "expected_reward": reward,
            "policy_type": "safe_rl_policy_baseline",
            "note": "Designed to be upgraded to PPO/DQN using incident feedback and MTTR reward.",
        }