import { useState, useEffect } from 'react'
import { Routes, Route } from 'react-router-dom';
import './App.css'

import Navbar from './UserView/Navbar/Navbar';
import LoginView from './LoginView/LoginView';
import LibrarianView from './UserView/LibrarianView/LibrarianView';
import StudentView from './UserView/StudentView/StudentView';  

export type Role = {
  [roleName : string] : number; // roleID : number
}

function App() {

  //  {"librarian" : 1}
  const [role, setRole] = useState<Role>();
  const [loggedIn, setLoggedIn] = useState<boolean>(false);
  const [accountMessage, setAccountMessage] = useState<string>("") 
  const [checkedOutBooks, setCheckedOutBooks] = useState<string[]>([])

  useEffect(() => {
      // Each time my account-message changes (only changes when the I send a POST request to 
      // sign-up / log-in the user): Send an HTML push-notification to the user showing them the reason they weren't able
      // to log-in / their log-in success
      // - HTML alert window-popup
      
      if (accountMessage !== "") {

        alert(accountMessage);
        setAccountMessage("") // Reset back to "" so user will get popup again for the exact same error (else same error => alert stays the same...)
      }

      console.log(checkedOutBooks);
      
  }, [accountMessage])

  return (
    <div className={loggedIn ? "home bg-gray-100" : "home"}>

      {
        loggedIn && <Navbar roleID={role === undefined ? -1 : Object.values(role)[0]}/>
      }

      {
        loggedIn && <Routes>
                      <Route path='/' element={<h1 className='absolute top-[50%] translate-y-[-50%] font-bold text-blue-500'> Welcome {Object.keys(role!)[0].split('').map((letter, idx) => (idx == 0 ? letter.toUpperCase() : letter)).join('')}! </h1>} />
                    </Routes>
      }


      {
        // @ts-expect-error
        !loggedIn ? <LoginView setRole={setRole} role={role} setLoggedIn={setLoggedIn} setAccountMessage={setAccountMessage} setCheckedOutBooks={setCheckedOutBooks}/> : (Object.values(role)[0] === 1 ? <LibrarianView roleID={Object.values(role)[0]}/> :  <StudentView roleID={role === undefined ? -1 : Object.values(role)[0]} checkedOutBooks={checkedOutBooks}/>)
      }

    </div>
  )
}

export default App
