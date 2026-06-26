import os
from neo4j import GraphDatabase
from knowledge_graph.kg_builder import load_kg

def export_to_neo4j():
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")
    kg = load_kg()
    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
        for node in kg["nodes"]:
            session.run("MERGE (n:AEGISNode {id: $id}) SET n.label=$label, n.name=$name",
                        id=node["id"], label=node.get("label", "Unknown"), name=node.get("name", node["id"]))
        for edge in kg["edges"]:
            session.run("""
                MATCH (a:AEGISNode {id: $source})
                MATCH (b:AEGISNode {id: $target})
                MERGE (a)-[r:RELATES_TO {relation: $relation}]->(b)
            """, source=edge["source"], target=edge["target"], relation=edge.get("relation", "RELATED_TO"))
    driver.close()
    print("Exported AEGIS KG to Neo4j.")

if __name__ == "__main__":
    export_to_neo4j()
