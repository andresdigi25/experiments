const express = require('express');
const app = express();
const port = 3000;

app.get('/', (req, res)=>{
    console.log('Hello World');
    res.send('Hello World');
})

app.listen(port, ()=>{
    console.log(`Server is running on port ${port}`);
})