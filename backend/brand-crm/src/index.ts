import "reflect-metadata";
import express from "express";
import { ApolloServer } from "apollo-server-express";
import { buildSchema } from "type-graphql";
import { AppDataSource } from "./data-source";
import { BrandResolver } from "./resolvers/BrandResolver";
import { DealResolver } from "./resolvers/DealResolver";
import { MediaKitResolver } from "./resolvers/MediaKitResolver";
import * as dotenv from "dotenv";

dotenv.config();

const PORT = process.env.PORT || 8003;

async function main() {
  // Initialize database
  await AppDataSource.initialize();
  console.log("Database connected");

  // Build GraphQL schema
  const schema = await buildSchema({
    resolvers: [BrandResolver, DealResolver, MediaKitResolver],
    validate: false
  });

  // Create Apollo Server
  const server = new ApolloServer({
    schema,
    context: ({ req }) => ({ req })
  });

  await server.start();

  // Create Express app
  const app = express();

  app.get("/", (req, res) => {
    res.json({
      name: "CreatorSync Brand CRM",
      version: "1.0.0",
      status: "operational"
    });
  });

  app.get("/health", (req, res) => {
    res.json({
      status: "healthy",
      timestamp: new Date().toISOString()
    });
  });

  // Apply Apollo middleware
  server.applyMiddleware({ app, path: "/graphql" });

  app.listen(PORT, () => {
    console.log(`🚀 Brand CRM Server ready at http://localhost:${PORT}`);
    console.log(`📊 GraphQL endpoint: http://localhost:${PORT}/graphql`);
  });
}

main().catch((error) => {
  console.error("Error starting server:", error);
  process.exit(1);
});
