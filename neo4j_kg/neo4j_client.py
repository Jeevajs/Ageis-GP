from neo4j import GraphDatabase
from neo4j_kg.neo4j_config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE

class Neo4jClient:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    def close(self):
        self.driver.close()
    def run_query(self, query, params=None):
        params = params or {}
        with self.driver.session(database=NEO4J_DATABASE) as session:
            return [record.data() for record in session.run(query, params)]
    def test_connection(self):
        try:
            return {"connected": True, "result": self.run_query("RETURN 'connected' AS status")}
        except Exception as e:
            return {"connected": False, "error": str(e)}
