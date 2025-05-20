@description('Location for all resources')
param location string = resourceGroup().location

@description('Storage account name (must be globally unique, 3–24 lowercase)')
param storageAccountName string

@description('Cognitive Services account name (globally unique, 3–24 lowercase)')
param cognitiveName string

resource storage 'Microsoft.Storage/storageAccounts@2022-09-01' = {
  name: storageAccountName
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
  properties: { accessTier: 'Hot' }
}

resource cognitive 'Microsoft.CognitiveServices/accounts@2022-12-01' = {
  name: cognitiveName
  location: location
  sku: { name: 'S0' }
  kind: 'FormRecognizer'
  properties: { publicNetworkAccess: 'Enabled' }
}

output storageEndpoint string = storage.properties.primaryEndpoints.blob
output cognitiveEndpoint string = cognitive.properties.endpoint
output cognitiveKey string = listKeys(cognitive.id, cognitive.apiVersion).key1
