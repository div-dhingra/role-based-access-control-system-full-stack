// import './loginview.css' | paths are case-INsensitive
// A. cd /... ABSOLUTE PATH CD (/ means absolute, not relative)
// B. cd './'... | OR | cd ... === RELATIVE PATH CD (append this extension to the CURRENT PATH,
// and navigate towards it)

// For API-requests to my backend-API endpoint-urls [event listeners-already set up :)]
// import axios from "axios"
// ! NOTE: Axios is only needed for the backend (when I'm working with a 3rd-party API
// ! using a backend-layer for better application security to not expose my frontend API-keys), since 
// ! async-await fetches don't work in the backend NODE.JS-framework (async-await WITH 'FETCH' in the backend are still experimental).
// ! ^^ i.e.: FETCH-API IS STILL EXPERIMENTAL IN BACKEND NODE.JS :)
// ! BUT, for my Javascript-frontend, fetch with async-await works just fine :)

import { useState, useEffect } from "react"
import { MdWarning } from "react-icons/md"

import { Role } from "../App";

type LoginViewProps = {
    role : Role | undefined,
    setRole : (role : Role) => void,
    setLoggedIn : (loggedIn : boolean) => void,
    setAccountMessage : (msg : string) => void,
    setCheckedOutBooks : (checkedOutBooks : string[]) => void
}

const LoginView = ({role, setRole, setLoggedIn, setAccountMessage, setCheckedOutBooks} : LoginViewProps) => {

    // const [roleID, setRoleID] = useState<number>(2) // Default to student (2), unless otherwise specified
    
    const [userID, setUserID] = useState<string>("") 
    const [userName, setUserName] = useState<string>("") 
    const [password, setPassword] = useState<string>("") 

    // For role selection dropdown ('Liibrarian, Student') mapped to their roleID to do setRoleID(roleID) for .map((role, roleID))
    const [roleOptions, setRoleOptions] = useState<Role>({}) // [{}, {}]

    const [errorMessages, setErrorMessages] = useState<{[key : number] : string}>([0, 1, 2].reduce((obj : any, num) => {obj[num] = ""; return obj}, {}));
    // '.map' Converts array1 into a NEW ARRAY of array2 values. Instead, we must use reduce here to convert from an array to an object, value by value.
    
    // To dynamically choose which state-variable to change via our input-field mapping-function below
    const inputStates = [setUserID, setUserName, setPassword];

    // Map to input-boxes
    const inputFields : string[] = ["UserID", "Username", "Password", "RoleID"];

    // Get list of role_id's
    useEffect(() => {

        const getRoles = async () => {
            const backend_url = "http://127.0.0.1:5000"
            const requestData = {
                method: "GET",
                headers: {
                    "Content-Type" : "application/json"
                }
                // body : JSON.stringify({ : , : }) for arg-request
            }

            try {
                const response = await fetch(`${backend_url}/api/roles`, requestData)
                const res = await response.json()
                const data = res.data
                // If not 200-response-code
                if (!response.ok) { 
                    throw new Error(`${response.status}`)
                }
                
                // @ts-expect-error
                let roleNameToIDObj = data.reduce((accumulatedRes : any, currRole) => {
                    // To convert betweeen different data-types, i.e. from array of elements to object of key-value-pairs
                    // Array transforms each individual element, but still maps it to the EXACT SAME INDEX in a RESULTING ARRAY (i.e. 
                    // not from array to object [different data-type]).
                    let key : string = currRole["role_name"];
                    let val : number = currRole["role_id"];
                    accumulatedRes[key] = val;
                    return accumulatedRes
                }, {}) //! MAKE SURE TO SPECIFY THE INITIAL VALUE OF THE ACCUMULATOR-RESULT-VARIABLE TO BE '{}' (i.e. CONVERTING [reducing] TO AN OBJECT)
                       //! -> IF I DON'T SPECIFY IT AS AN INITIALLY EMPTY-{}-OBJECT, THEN MY LOGIC WON'T WORK!!!

                // console.log(roleNameToIDObj) // .data?
                setRoleOptions(roleNameToIDObj)

            } catch(error) {
                console.error(error)
            }
        }

        getRoles()

    }, []) 

    // Function to verify constraints for the given input
    const checkInvalidInput = (inputField : string, inputVal : string) => {

        if (inputField === "UserID") {
            let newErrorMessages = errorMessages

            if (role === undefined) {
                newErrorMessages[0] = "Please select a role first";
            }

            else if (Object.keys(role)[0] === "librarian" && !(/^\d{4}$/.test(inputVal))) {
                newErrorMessages[0] = "User ID must be exactly 4 digits for Librarians";
                // setErrorMessages(prevData => ({
                //     ...prevData, // Spread previous contents of JSON-object
                //     0 : "UserID must be 4 digits for a Librarian, or 9 digits for a Student."
                // }));
            } 

            else if (Object.keys(role)[0] === "student" && !(/^\d{9}$/.test(inputVal))) {
                newErrorMessages[0] = "User ID must be exactly 9 digits for Students";
                // setErrorMessages(prevData => ({
                //     ...prevData, // Spread previous contents of JSON-object
                //     0 : "UserID must be 4 digits for a Librarian, or 9 digits for a Student."
                // }));
            } 
            
            // Delete it if it is no longer an error
            // If no longer an error, set errorMessage to a blank string for this index
            else {
                newErrorMessages[0] = "";
            }
            // else if (0 in newErrorMessages) {
            //     delete newErrorMessages[0]
            // }
            
            // Update error-messages object
            setErrorMessages(newErrorMessages)
        }

        if (inputField === "Username") {

            console.log(inputVal, "Test")

            let newErrorMessages = errorMessages
            if (inputVal === "") {
                newErrorMessages[1] = "Username must not be empty"
                    // setErrorMessages(prevData => ({
                    //     ...prevData, // Spread previous contents of JSON-object
                    //     1 : "Username must not be empty"
                    // }));
            } 

            // If no longer an error, set errorMessage to a blank string for this index
            else {
                newErrorMessages[1] = ""
            }
            // else if (1 in newErrorMessages) {
            //     delete newErrorMessages[1]
            // }

            // Update error-messages object
            setErrorMessages(newErrorMessages)

        }
       
        else if (inputField === "Password") {

            let newErrorMessages = errorMessages
            if (inputVal === "") {
                newErrorMessages[2] = "Password must not be empty"
                    // setErrorMessages(prevData => ({
                    //     ...prevData, // Spread previous contents of JSON-object
                    //     1 : "Username must not be empty"
                    // }));
            } 

            // If no longer an error, set errorMessage to a blank string for this index
            else {
                newErrorMessages[2] = ""
            }
            // else if (2 in newErrorMessages) {
            //     delete newErrorMessages[2]
            // }

            // Update error-messages object
            setErrorMessages(newErrorMessages)
        }

        // None of the above conditions returned True (i.e. input-field is valid)
        // --> return 'False' for invalidity (i.e. Valid)
        // Role-ID is from the dropdown 
        // -> Based on my typing, TS will return an error if the role_id =! 1 or 2 (+ backend input-validation
        // to verify that role_id == 1 OR 2 only, for intercepted/direct, frontend-input-validation-bypassing
        // API-requests
        // return -1 // Falase

    }

    // To Login/Signup the user (post-request)
    // NOTE: is_active_account, books_overdue is set by my backend (no need to pass it in as args)
    // Password hash is (obv) stored in my database for each user :)
    //  role_id = request_header_data.get("role_id")
    // user_id = request_header_data.get("user_id") # librarian/student ID # (3 digits vs. 9 digits | validation again in 
    //     # backend for intercepted, modified requests)
    //     user_name =  request_header_data.get("user_name")
    //     password = request_header_data.get("password") # For security, store hash of password (not password explicitly) in my database
    const processUser = async (userID : string, userName : string, password : string | undefined, roleID : number) => {
  
        const backend_url = "http://127.0.0.1:5000"
        const requestData = {
            method: "POST",
            headers: {
                "Content-Type" : "application/json"
            }, 
            body : JSON.stringify({ 
                "role_id" : roleID,
                "user_id" : userID,
                "user_name" : userName,
                "password" : password,  
            })
        }
  
        try {
            const response = await fetch(`${backend_url}/api/users`, requestData)
            const res = await response.json() // Convert JSON-object to JS-USABLE Object
            console.log(res)
            // If not 200-response-success-code
            // Ex. Error-Message 201 (invalid password error)
            // Ex. Error-Message 409 (password taken [i.e., conflict] error)
            if (!response.ok) { 
                setAccountMessage(res.error) // HTML-alert: All fields are necessary, etc. [i.e. user wasn't able to make an account]
                throw new Error(res.error)
            }
            
            console.log(res.message) // Welcome Back or Congratulations! You have made an account (Returnign Log-In vs. New Signup)

            // IFF no error prior :)
            setLoggedIn(true)
            setCheckedOutBooks(res.book_checkouts)
            // console.log(res)
            setAccountMessage(res.message)

        } catch(error) {
            console.error(error)
        }
    }

    // useEffect(() => {
        
    //     // Skip initial render
    //     if (role !== undefined) {
    //         checkInvalidInput("UserID", userID);
    //     }
    // }, [role])

    // To synchronize state-changes (since onChange has a delay b/c state-variables change asynchronously),
    // i.e.: STATE-ALIGNMENT :)
    const handleChange = (e : React.ChangeEvent<HTMLInputElement>, idx : number) => {
        let newVal : string = e.target.value;
        inputStates[idx]((prevVal) => {
            console.log(prevVal);
            return newVal; 
        });
    }

    const handleRoleSelection = (event : any) => {
        setRole({ [event.target.value] : roleOptions[event.target.value]})
    }

    return (

        <div className="flex flex-col gap-2"> 

             {/* // Role-ID will be from a dropdown, hence not included below.
                // Minimal code [NON-COMPLEX COMPONENT], so I don't
                // need a separate modular-component-function-folder for it
                // (just do it here, in line)
                // * <RoleIDDropdown/> */}
                {/* OnClick(()=>setRoleID(...))  */}
                {/* `Select ${inputFields[3]} Below` */}

            <div className="flex flex-col w-[360px] h-[50px]"> 
                <select id="options" value={role === undefined ? "" : Object.keys(role)[0]} className="rounded-md bg-white ring-2 ring-gray-300 text-black text-md h-[30px]" onChange={handleRoleSelection} >
                        <option value="" disabled>Select role</option> {/* Placeholder option | Disabled so it can't be re-selected */}
                        {/* Object.entries({key-val-pairs-object} to return an array of each individual 'key-val' pair as an element (each an elemental-array of [key, val])) */}
                        {Object.entries(roleOptions).map((roleDetails : any, idx) => {
                            return (
                                // NOTE: EVENT.TARGET.VALUE BE REPRESENT WHATEVER IS IN THIS 'value' FIELD
                                // --> SO MY 'ROLE'-type [role_name : roleID] logic isn't even necessary...
                                <option key={idx} value={`${roleDetails[0]}`}>
                                    {roleDetails[0]}
                                </option>
                            )
                            // role["role_name"]
                        })}
                </select>
            </div>
            
            {/* Input Boxes */}
            <div className="flex flex-col justify-start">

                {    
                    // Slice is exclusive
                    inputFields.slice(0, 3).map((inputField : string, idx : number) => (
                        <div key={inputField} className="flex flex-col w-[360px] h-[65px]"> 
                            <input onChange = {(event) => {checkInvalidInput(inputField, event.target.value); handleChange(event, idx);}} className="rounded-md bg-white ring-2 ring-gray-300 text-black h-[30px] p-1.5" />
                            
                            {(errorMessages[idx] !== "") && 
                                (
                                    <div className="flex flex-row gap-1 items-center mt-[2.5px]">
                                        {/* <Icon as={MdWarning} size={"sm"} color="red.500"/> */}
                                        <MdWarning className="mt-[1px]" style={{"color" : "rgb(250, 0, 0)"}} size={"13.5px"} />
                                        <p className="text-red-500 text-xs text-left"> {`${errorMessages[idx]}`} </p>
                                    </div>
                                )
                            }
                        </div>
                        // inputStates[idx](event.value);
                    ))
                }

                {/* Empty === no error-messages */}
                <button className={!(Object.values(errorMessages).every(msg => msg === "") && (userID !== "" && userName !== "" && password !== "" && role !== undefined)) ? "bg-gray-300 text-white font-bold" : "bg-blue-600 text-white font-bold"}
                    /* @ts-ignore | the button will be disabled when roleID == Null anyway + our backend-input-validation handles frontend-validation bypasses (i.e. returned error-message :))*/
                    onClick={() => {processUser(userID, userName, password, Object.values(role)[0])}} disabled={!(Object.values(errorMessages).every(msg => msg === "") && (userID !== "" && userName !== "" && password !== "" && role !== undefined))}>
                        Submit 
                </button>

            </div>

        </div>

    )
}

export default LoginView