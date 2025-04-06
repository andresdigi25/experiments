const fs = require('fs');

fs.readFile('books.json',function(err,data){
    if(err){
        console.log(err);
    }else{
        const books = JSON.parse(data);
        console.log(books);
    }
});