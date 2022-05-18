<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->
(HACK to help debugging. Remove later)

In Python console:
```python
pprint.PrettyPrinter(indent=2).pprint(DATA_ddo.as_dictionary())

{
  'id': 'did:op:4568CA67353c0db9eA07Fdf85Dc051468cF7397f',
  'dataToken': '0x4568CA67353c0db9eA07Fdf85Dc051468cF7397f',
  'publicKey': [
    {
      'id': 'did:op:4568CA67353c0db9eA07Fdf85Dc051468cF7397f',
      'owner': '0xe2DD09d719Da89e5a3D0F2549c7E24566e947260',
      'type': 'EthereumECDSAKey'
    }],
  
  'service': [
    {
      'type': 'metadata',
      'index': 0,
      'serviceEndpoint': 'http://localhost:5000/api/v1/aquarius/assets/ddo/did:op:4568CA67353c0db9eA07Fdf85Dc051468cF7397f',
      'attributes': {
        'encryptedFiles': '0x049031...47d0gsgdsasdoidsoimaoimw9494214', #large blob
        'main': {
          'type': 'dataset'
          'files': [
	    {
              'index': 0
	      'contentType': 'text/text',
	    }],
          'license': 'CC0',
          'name': 'branin',
	  'author': 'Trent',
          'dateCreated': '2019-12-28T10:55:11Z'
      } }
    },

    {
      'type': 'access'
      'index': 3,
      'serviceEndpoint': 'http://localhost:8030',
      'attributes': {
        'main': {
          'creator': '0xe2DD09d719Da89e5a3D0F2549c7E24566e947260',
          'datePublished': '2019-12-28T10:55:11Z',
          'name': 'DATA_dataAssetAccessServiceAgreement',
          'timeout': 86400,
	  'cost': 1.0
    } } }
  ],

  '@context': 'https://w3id.org/did/v1',
  'created': '2021-08-24T11:01:32Z',
  'authentication': [
    {
      'publicKey': 'did:op:4568CA67353c0db9eA07Fdf85Dc051468cF7397f',
      'type': 'RsaSignatureAuthentication2018'
     } ],
  'proof': {
    'checksum':
    {
      '0': '667a2fd0ec238a4134a2b47b76c0e9359f5e66e55e861fe81ecddf23bfab1dcf',
      '3': '5188714e14e4aafbd56101f7406a96b912f250e2d75fdd7f3c00801cd64e71f8'
    },
    'created': '2021-08-24T11:01:32Z',
    'creator': '0xe2DD09d719Da89e5a3D0F2549c7E24566e947260',
    'signatureValue': '0x17d91de3829..',
    'type': 'DDOIntegritySignature'
    }
  }
}
```
