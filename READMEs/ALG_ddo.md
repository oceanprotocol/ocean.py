<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->
(HACK to help debugging. Remove later)

In Python console:
```python
pprint.PrettyPrinter(indent=2).pprint(ALG_ddo.as_dictionary())

{
  '@context': 'https://w3id.org/did/v1',
  'authentication': [
    {
      'publicKey': 'did:op:beD519EF79eE3b06b94751dFC8ce62587b8de6Cf',
      'type': 'RsaSignatureAuthentication2018'
    }],
    
  'created': '2021-08-24T11:57:45Z',
  'dataToken': '0xbeD519EF79eE3b06b94751dFC8ce62587b8de6Cf',
  'id': 'did:op:beD519EF79eE3b06b94751dFC8ce62587b8de6Cf',
  
  'proof': {
    'checksum': {
      '0': '09db9193f00de71305d5100d3a2c7d2e08a2a81e958fefe6defb7391ed46fca8',
      '3': '96f72f4c84d8799e3cc2017e202c4cabe387efb4f43a6c07d2a16ffad7f70bdf'
    },
    'created': '2021-08-24T11:57:45Z',
    'creator': '0xe2DD09d719Da89e5a3D0F2549c7E24566e947260',
    'signatureValue': '0x8d4b0c2ae7485e67bb43c6e32a4d4058861807909b9064c242f24c2bc288c6b378cd8fd585302c90cccf449e3cbda3eff58850f4d240680e03f8ba68414180d61c',
    'type': 'DDOIntegritySignature'
  },
  'publicKey': [
    {
      'id': 'did:op:beD519EF79eE3b06b94751dFC8ce62587b8de6Cf',
      'owner': '0xe2DD09d719Da89e5a3D0F2549c7E24566e947260',
      'type': 'EthereumECDSAKey'
    }],
    
  'service': [
    {
      'attributes': {
        'encryptedFiles': '0x04939dd7...7ab9da', #large blob
        'main': { 'author': 'Trent',
        'dateCreated': '2020-01-28T10:55:11Z',
        'files': [
	  {
	    'contentType': 'text/text',
            'index': 0
	  }],
        'license': 'CC0',
        'name': 'gpr',
        'type': 'algorithm'
      } },
      'index': 0,
      'serviceEndpoint': 'http://localhost:5000/api/v1/aquarius/assets/ddo/did:op:beD519EF79eE3b06b94751dFC8ce62587b8de6Cf',
      'type': 'metadata'
    },
    
    {
      'attributes': {
        'main': {
	  'cost': 1.0,
          'creator': '0xe2DD09d719Da89e5a3D0F2549c7E24566e947260',
          'datePublished': '2020-01-28T10:55:11Z',
          'name': 'ALG_dataAssetAccessServiceAgreement',
          'timeout': 86400
      } },
      'index': 3,
      'serviceEndpoint': 'http://localhost:8030',
      'type': 'access'
  }]
}
```