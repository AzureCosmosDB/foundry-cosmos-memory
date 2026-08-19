targetScope = 'resourceGroup'

@description('Location for all resources.')
param location string = resourceGroup().location

@description('A stable unique suffix appended to resource names.')
param resourceToken string = toLower(uniqueString(subscription().id, resourceGroup().id, location))

@description('Object ID of the user or service principal running azd.')
param principalId string

@description('Principal type used for role assignments.')
@allowed([ 'User', 'ServicePrincipal' ])
param principalType string = 'User'

@description('Chat model deployment name.')
param chatModelName string = 'gpt-4o-mini'

@description('Chat model version.')
param chatModelVersion string = '2024-07-18'

@description('Embedding model deployment name.')
param embeddingModelName string = 'text-embedding-3-large'

@description('Cosmos DB database name for memory.')
param cosmosDatabaseName string = 'ai_memory'

resource aiAccount 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' = {
  name: 'aif-${resourceToken}'
  location: location
  kind: 'AIServices'
  sku: {
    name: 'S0'
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    allowProjectManagement: true
    customSubDomainName: 'aif-${resourceToken}'
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: false
  }
}

resource aiProject 'Microsoft.CognitiveServices/accounts/projects@2025-04-01-preview' = {
  parent: aiAccount
  name: 'proj-${resourceToken}'
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {}
}

resource chatDeployment 'Microsoft.CognitiveServices/accounts/deployments@2025-04-01-preview' = {
  parent: aiAccount
  name: chatModelName
  sku: {
    name: 'GlobalStandard'
    capacity: 50
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: chatModelName
      version: chatModelVersion
    }
  }
}

resource embeddingDeployment 'Microsoft.CognitiveServices/accounts/deployments@2025-04-01-preview' = {
  parent: aiAccount
  name: embeddingModelName
  dependsOn: [ chatDeployment ]
  sku: {
    name: 'Standard'
    capacity: 50
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: embeddingModelName
      version: '1'
    }
  }
}

resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2024-12-01-preview' = {
  name: 'cosmos-${resourceToken}'
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    enableFreeTier: false
    disableLocalAuth: true
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    capabilities: [
      {
        name: 'EnableNoSQLVectorSearch'
      }
      {
        name: 'EnableNoSQLFullTextSearch'
      }
    ]
  }
}

resource cosmosDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-12-01-preview' = {
  parent: cosmosAccount
  name: cosmosDatabaseName
  properties: {
    resource: {
      id: cosmosDatabaseName
    }
  }
}

resource cosmosDataContributor 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2024-12-01-preview' = {
  parent: cosmosAccount
  name: guid(cosmosAccount.id, principalId, 'data-contributor')
  properties: {
    roleDefinitionId: '${cosmosAccount.id}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002'
    principalId: principalId
    scope: cosmosAccount.id
  }
}

resource foundryUserRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(aiAccount.id, principalId, 'foundry-user')
  scope: aiAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '53ca6127-db72-4b80-b1b0-d745d6d5456d')
    principalId: principalId
    principalType: principalType
  }
}

resource foundryProjectUserRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(aiProject.id, principalId, 'foundry-user')
  scope: aiProject
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '53ca6127-db72-4b80-b1b0-d745d6d5456d')
    principalId: principalId
    principalType: principalType
  }
}

resource openAiUserRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(aiAccount.id, principalId, 'openai-user')
  scope: aiAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd')
    principalId: principalId
    principalType: principalType
  }
}

output AZURE_LOCATION string = location
output COSMOS_ENDPOINT string = cosmosAccount.properties.documentEndpoint
output COSMOS_DATABASE string = cosmosDatabaseName
output FOUNDRY_ENDPOINT string = 'https://${aiAccount.name}.services.ai.azure.com'
output FOUNDRY_PROJECT_ENDPOINT string = aiProject.properties.endpoints['AI Foundry API']
output FOUNDRY_PROJECT_NAME string = aiProject.name
output CHAT_MODEL string = chatModelName
output EMBEDDING_MODEL string = embeddingModelName
output AZURE_AI_ACCOUNT_NAME string = aiAccount.name
