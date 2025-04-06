const fs = require("fs");

const books =
{
    title: "The Adventures of Tom Sawyer",
    genre: "Adventure",
    type: "Novel",
    pages: 208
}
console.log("Books: ", books);

const jsonBooks = JSON.stringify(books,null, 2);
console.log("JSON Books: ", jsonBooks);

fs.writeFile("books-written.json", jsonBooks, 'utf-8', (err) => {
    if(err){
        console.log("Error writing to file ", err);
    } else {
        console.log("Data written to file");
    }
});