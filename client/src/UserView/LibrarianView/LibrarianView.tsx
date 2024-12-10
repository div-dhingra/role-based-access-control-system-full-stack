import "./LibrarianView.css";
import LibrarianDashboard from "./LibrarianDashboard/LibrarianDashboard";
import BookCatalog from "../BookCatalog/BookCatalog";
import {Routes, Route} from 'react-router-dom';

type LibrarianViewProps = {
    roleID : number;
}

const LibrarianView = ({roleID} : LibrarianViewProps) => {

    return (
        <div className="bg-gray-100 w-full h-full flex flex-row lib-view overflow-scroll"> 
            <Routes> 
                <Route path = '/user-info' element = {<LibrarianDashboard roleID={roleID}/>}/>
                <Route path = '/books' element = {<BookCatalog roleID={roleID}/>}/>
            </Routes>
        </div>
    )
}

export default LibrarianView;