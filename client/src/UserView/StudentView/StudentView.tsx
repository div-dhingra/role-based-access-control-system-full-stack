import BookCatalog from "../BookCatalog/BookCatalog";
import {Routes, Route} from 'react-router-dom';

type StudentViewProps = {
    roleID: number,
    checkedOutBooks: string[]
}

const StudentView = ({roleID, checkedOutBooks} : StudentViewProps) => {
    
    return (
        <div className="bg-gray-100 w-full h-full flex flex-row lib-view overflow-scroll"> 

            <Routes>
                <Route path = '/books' element = {<BookCatalog roleID={roleID} checkedOutBooks={checkedOutBooks}/>}/>
            </Routes>
        </div>
    )
}

export default StudentView;