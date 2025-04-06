
# POST Request  
import requests 
  
url = "https://fruits-api.netlify.app/graphql"
  
body = """ 
mutation { 
  addFruit( 
    id: 1 
    scientific_name: "mangifera" 
    tree_name: "mangifera indica" 
    fruit_name: "Mango" 
    family: "Anacardiaceae" 
    origin: "India" 
    description: "Mango is yellow" 
    bloom: "Summer" 
    maturation_fruit: "Mango" 
    life_cycle: "100" 
    climatic_zone: "humid" 
  ) { 
    id 
    scientific_name 
    tree_name 
    fruit_name 
    origin 
  } 
} 
"""
  
response = requests.post(url=url, json={"query": body}) 
print("response status code: ", response.status_code) 
if response.status_code == 200: 
    print("response : ",response.content) 