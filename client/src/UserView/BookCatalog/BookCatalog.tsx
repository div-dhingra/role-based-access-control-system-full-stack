import { useEffect, useState } from "react"

type BookCatalogProps = {
    roleID: number,
    checkedOutBooks? : string[],
    userID? : string
}

const BookCatalog = ({roleID, checkedOutBooks, userID} : BookCatalogProps) => {

    const [books, setBooks] = useState([])
    const bookInfoTags = {
        "book_isbn_id" : "ISBN #", 
        "title" : "Title", 
        "author" : "Author", 
        "published_year": "Published", 
        "total_book_count" : "Total Copies",
        "available_count": "Available Copies"
    };

    const getBookCatalog = async () => {
        
        const backend_url = "http://127.0.0.1:5000";

        // Get requests don't allow request-'body' — use url-query-params instead :)
        const queryParams = {
            role_id: `${roleID}`, // Convert integer to string for url-query-params :)
            table_name: "books", 
            action: "SELECT",
            column_field: "*"
        }
        const queryString = new URLSearchParams(queryParams).toString();
        const requestData = {
            method: "GET",
            headers: {
                "Content-Type" : "application/json"
            }
        }

        try {
            const response = await fetch(`${backend_url}/api/books?${queryString}`, requestData)
            console.log(response)
            // If not 200-response-code
            if (!response.ok) { 
                throw new Error(`${response.status}`)
            }

            const res = await response.json()
            let books = res.books

            console.log(books)
            setBooks(books)

        } catch(error) {
            console.error(error)
        }
    }

    const deleteBook = async (isbnID : string) => {

        const backend_url = "http://127.0.0.1:5000";
        const requestData = {
            method: "DELETE",
            headers: {
                "Content-Type" : "application/json",
            }, 
            body: JSON.stringify({
                role_id: `${roleID}`, // Convert integer to string for url-query-params :)
                table_name: "books", 
                action: "DELETE",
                column_field: "N/A"
            })
        }

        try {
            const response = await fetch(`${backend_url}/api/books/${isbnID}`, requestData)
            const res = await response.json() // Convert into JS-usable Object :)

            // If not 200-response-code
            if (!response.ok) { 
                throw new Error(`${res.error}`)
            }
        
            console.log(res.message);

        } catch(error) {
            alert(error)
            console.error(error)
        }
    }

    const borrowBook = async (userID : string, isbnID : string, roleID : string) => {

        const backend_url = "http://127.0.0.1:5000";
        const requestData = {
            method: "PATCH",
            headers: {
                "Content-Type" : "application/json",
            },
            body: JSON.stringify({
                role_id: roleID,
                table_name: "user_book_checkouts",
                action: "INSERT",
                column_field: "N/A",
                book_isbn_id: isbnID
            })
        }

        try {
            const response = await fetch(`${backend_url}/api/users/${userID}/borrow-book`, requestData)
            console.log(response)
            // If not 200-response-code
            if (!response.ok) { 
                throw new Error(`${response.status}`)
            }

            const res = await response.json()
            console.log(res.message)

        } catch(error) {
            console.error(error)
        }
    }

    const returnBook = async () => {
        console.log("Book returned");
    }
    
    useEffect(() => {
        getBookCatalog()
    }, []);

    return (
        <div className="flex flex-row flex-wrap gap-8 ml-5 overflow-scroll p-8"> 
            {books.map((book) => {
                return (
                    // @ts-expect-error
                    <ul key={Object.values(book)} className='flex flex-col justify-center gap-2 align-center rounded-md ring-2 ring-blue-500 w-[22.5%] text-black p-2'> 
                        {   
                            (Object.keys(book)).map((detail : string, idx : number) => (
                                                                                    // @ts-expect-error 
                                                                                    bookInfoTags[detail] !== "Active Status") && 
                                                                                        <li key={book[detail]} className="text-center text-xs text-wrap">
                                                                                            {/* @ts-expect-error  */}
                                                                                            <span className="font-bold" key={idx}> {bookInfoTags[detail]}: </span> 
                                                                                            {`${detail === "role_id" ? (book[detail] == "2" ? "Student" : "Librarian") : 
                                                                                                    // @ts-expect-error 
                                                                                                typeof book[detail] === "object" ? (book[detail].length === 0 ? "N/A" :
                                                                                                        // @ts-expect-error  
                                                                                                        book[detail].length) : book[detail]}`} 
                                                                                        </li>)
                        }

                        {
                            roleID == 1 ? (
                                <div className="flex flex-row justify-evenly align-center">
                                    <button className={"p-1 mt-1 w-[40%] self-center text-xs text-white bg-blue-500"} onClick={() => {setBooks([]); /* updateBook(book["book_isbn_id"]); */ getBookCatalog();}}> 
                                        Update Book
                                    </button> 
                                    
                                    <button className={"p-1 mt-1 w-[40%] self-center text-xs text-white bg-red-500"} onClick={() => {setBooks([]); deleteBook(book["book_isbn_id"]); getBookCatalog();}}> 
                                        Delete Book
                                    </button>
                                </div>
                            ) : (
                                <div className={checkedOutBooks!.includes(book["book_isbn_id"]) ? "flex flex-row justify-evenly align-center" : "flex flex-row justify-center align-center"}>
                                     <button className={"p-1 mt-1 w-[40%] self-center text-xs text-white bg-green-500"}> 
                                        Borrow Book
                                    </button>
                                    
                                    {   
                                        checkedOutBooks!.includes(book["book_isbn_id"]) && (
                                            <button className={"p-1 mt-1 w-[40%] self-center text-xs text-white bg-red-500"}> 
                                                Return Book
                                            </button>
                                        )
                                    }
                                </div>

                            )
                        }
                    </ul>
                )
            })} 
        </div>
    )

}

export default BookCatalog;