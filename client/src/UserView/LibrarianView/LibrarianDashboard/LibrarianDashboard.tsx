import { useEffect, useState } from "react"
import './LibrarianDashboard.css'

import { IoMdRefresh } from "react-icons/io";

type LibrarianDashboardProps = {
    roleID : number
}

const LibrarianDashboard = ({roleID} : LibrarianDashboardProps) => {

    const [displayOption, setDisplayOption] = useState<"Approvals" | "Excessive Overdue" | "All Users">("All Users");
    const [displayedUsers, setDisplayedUsers] = useState([]);

    const getDisplay = async () => {
        const backend_url = "http://127.0.0.1:5000"
        let url_extension : string = ""
        const requestData = {
            method: "GET",
            headers: {
                "Content-Type" : "application/json"
            }
        }
        
        // Fetch list of excessive books (>3) overdue users, so librarian can DE-PROVISION (i.e. de-activate)
        // them.
        if (displayOption == "Excessive Overdue") {
            url_extension = "?status=excessive-overdue";
        }
        
        // Fetch users that need to be approved to access their account (New users, users back within <=3 overdue books-limit)
        else if (displayOption == "Approvals") {
           url_extension= "?status=needs-approval";
        }

        try {
            const response = await fetch(`${backend_url}/api/users${url_extension}`, requestData)

            const res = await response.json()
            const users = res.users
            // If not 200-response-code
            if (!response.ok) { 
                throw new Error(`${response.status}`)
            }
            
            console.log(users)
            setDisplayedUsers(users)
        } catch(error) {
            console.error(error)
        }
    }

    const updateUserAccountStatus = async (userID : string, newActiveStatus : boolean) => {
        const backend_url = "http://127.0.0.1:5000";
        const requestData = {
            method: "PATCH",
            headers: {
                "Content-Type" : "application/json",
            },
            body : JSON.stringify({ 
                role_id : roleID, 
                table_name : "users",
                action: "UPDATE",
                column_field : "is_active_account",
                new_active_status : newActiveStatus}) 
        }
    
        try {
            const response = await fetch(`${backend_url}/api/${userID}/update-active-status`, requestData)
            const res = await response.json()
            // If not 200-response-code
            if (!response.ok) { 
                throw new Error(`${response.status}`)
            }
            
            // Active Status changed to 'T/F'...
            console.log(res.message)

        } catch(error) {
            console.error(error)
        }
    }

    useEffect(() => {

        getDisplay()
        console.log(displayOption)

    }, [displayOption])

    const showDisplay = () => {

        const userInfoTags = {
                                "user_id" : "User ID", 
                                "role_id" : "Role", 
                                "user_name" : "Username", 
                                "is_active_account": "Active Status", 
                                "books_overdue" : "Books Overdue"
                            };

        if (displayOption == "All Users") {
            return ( 
                <div className="flex flex-row flex-wrap gap-4 ml-6"> 
                    {displayedUsers.map((user, idx) => {
                        return (
                            <ul className='rounded-md ring-2 ring-gray-300 w-[30%]' key={idx}> 
                                {   
                                    // @ts-expect-error 
                                    (Object.keys(user).reverse()).map((detail : string) => <li key={user[detail]} className="text-center text-sm"> <span className="font-bold"> {userInfoTags[detail]}: </span> {`${detail === "role_id" ? (user[detail] == "2" ? "Student" : "Librarian") : typeof user[detail] === "object" ? (user[detail].length === 0 ? "N/A" : user[detail].length) : user[detail]}`} </li>)
                                }
                            </ul>
                        )
                    })} 
                </div>
            )

        } else if (displayOption == "Excessive Overdue") {

            console.log(displayedUsers)

            return (
                <div className="flex flex-row flex-wrap gap-4 ml-6"> 
                    {displayedUsers.map((user, idx) => {
                        return (
                            <ul className='flex flex-col justify-center gap-2 align-center rounded-md ring-2 ring-gray-300 w-[27.5%] h-[125px]' key={idx}> 
                                {   
                                    // @ts-expect-error 
                                    (Object.keys(user).reverse()).map((detail : string) => ((userInfoTags[detail] !== "Role" && 
                                                                                            // @ts-expect-error 
                                                                                            userInfoTags[detail] !== "Active Status") && 
                                                                                                <li key={user[detail]} className="text-center text-sm">
                                                                                                    {/* @ts-expect-error  */}
                                                                                                     <span className="font-bold"> {userInfoTags[detail]}: </span> 
                                                                                                     {`${detail === "role_id" ? (user[detail] == "2" ? "Student" : "Librarian") : 
                                                                                                            // @ts-expect-error 
                                                                                                           typeof user[detail] === "object" ? (user[detail].length === 0 ? "N/A" :
                                                                                                                // @ts-expect-error  
                                                                                                                user[detail].length) : user[detail]}`} 
                                                                                                </li>))
                                }

                                <button className={user["is_active_account"] === false ? "p-1 m-0 w-[50%] self-center text-xs text-white bg-red-300" : "p-1 m-0 w-[50%] self-center text-xs text-white bg-red-500"} disabled={user["is_active_account"] === false} onClick={() => {updateUserAccountStatus(user["user_id"], false)}}> 
                                    Deactivate
                                </button>
                            </ul>
                        )
                    })} 
                </div>
            )

        } else if (displayOption == "Approvals") {

            console.log(displayedUsers)

            return (
                <div className="flex flex-row flex-wrap gap-4 ml-6"> 
                    {displayedUsers.map((user, idx) => {
                        return (
                            <ul className='rounded-md ring-2 ring-gray-300 w-[30%] flex flex-col p-2 gap-1' key={idx}> 
                                {   
                                    (Object.keys(user).reverse()).map((detail : string) => ( <li key={user[detail]} className="text-center text-sm">
                                                                                                    {/* @ts-expect-error  */}
                                                                                                     <span className="font-bold"> {userInfoTags[detail]}: </span> 
                                                                                                     {`${detail === "role_id" ? (user[detail] == "2" ? "Student" : "Librarian") : 
                                                                                                            // @ts-expect-error 
                                                                                                           typeof user[detail] === "object" ? (user[detail].length === 0 ? "N/A" :
                                                                                                                // @ts-expect-error  
                                                                                                                user[detail].length) : user[detail]}`} 
                                                                                                </li>
                                                                                        ))
                                }

                                <button className={"p-1 mt-1.5 w-[50%] self-center text-xs text-white bg-green-500"} onClick={() => {updateUserAccountStatus(user["user_id"], true)}}> 
                                    Activate
                                </button>
                            </ul>
                        )
                    })} 
                </div>
            )


        }

    }

    const options : string[] = ["Approvals", "Excessive Overdue", "All Users"].reverse();

    return (
        <div className="lib-dashboard bg-white rounded-3xl text-black flex flex-col gap-3 p-[1em] mt-8">
            <div className="w-full flex flex-row justify-between align-start mb-[0.65em] sticky"> 
                <IoMdRefresh className="mt-[0.15em] w-[15%] cursor-pointer" size={"20px"} onClick={() => {setDisplayedUsers([]); getDisplay();}}/>

                <ul className="flex flex-row justify-around w-[85%]">
                    {options.map((option) => <li className = {displayOption === option ? "text-blue-500 font-bold cursor-pointer" : "text-black font-bold cursor-pointer"} 
                                                // @ts-expect-error
                                                onClick={() => {setDisplayedUsers([]); setDisplayOption(option);}}> 
                                                {option} 
                                            </li>
                    )}
                </ul>
            </div>
            {showDisplay()}
        </div>
    )

}

export default LibrarianDashboard