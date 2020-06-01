# Quickstart: Simple Flow 

This stripped-down flow shows the essence of Ocean. Just downloading, no metadata.

Here's the steps.
1. Alice publishes a dataset (= publishes a datatoken contract)
1. Alice hosts the dataset
1. Alice mints 100 tokens
1. Alice transfers 1 token to Bob
1. Bob consumes dataset

Let's go through each step.

## 0. Installation

If you haven't installed yet:
```console
pip install ocean-lib
```

## 1. Alice publishes a dataset (= publishes a datatoken contract)

For now, you're Alice:) Let's proceed.

```python
from ocean_lib import Ocean
config = {
   'network' : 'rinkeby',
   'privateKey' : '8da4ef21b864d2cc526dbdb2a120bd2874c36c9d0a1fb7f8c63d7f7a8b41de8f',
}
ocean = Ocean.Ocean(config)
token = ocean.datatoken.create('localhost:8030',account)
dt_address = token.getAddress()
print(dt_address)
```

## 2. Alice hosts the dataset

A local providerService is required, which will serve just one file for this demo.
Let's create the file to be shared:
```
touch /var/mydata/myFolder1/file
````

Run the providerService:
(given that ERC20 contract address from the above is 0x1234)

```
ENV DT="{'0x1234':'/var/mydata/myFolder1'}"
docker run @oceanprotocol/provider-py -e CONFIG=DT
```


## 3. Alice mints 100 tokens

```python
token.mint(100)
```

## 4. Alice transfers 1 token to Bob

```python
bob_address = '0x0ecd5f934768df296EfB58802418fD68B53873C0'
token.transfer(bob_address, 1)
```

## 5. Bob consumes dataset

Now, you're Bob:)

```python
const bob_config={
   network: 'rinkeby',
   privateKey:'1234ef21b864d2cc526dbdb2a120bd2874c36c9d0a1fb7f8c63d7f7a8b41de8f' #corresponds to bob_address 
}
bob_ocean = Ocean(bob_config)
token = bob_ocean.getToken(dt_address)
_file = token.download(account)
```
