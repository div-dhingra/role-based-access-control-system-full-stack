import { PiBooks } from "react-icons/pi";
import { FiUser } from "react-icons/fi";
import { Link } from "react-router-dom";

type NavbarProps = {
    roleID : number
}

const Navbar = ({roleID} : NavbarProps) => {

    return (

        <nav className="p-2 mt-2 w-[30vw]"> 
            <ul className={roleID === 1 ? "flex flex-row justify-around align-center bg-white rounded ring-2" : "flex flex-row justify-center align-center bg-white rounded ring-2"}> 
                {roleID === 1 && <li className="cursor-pointer"> <Link to='/user-info'> <FiUser color={"black"} size={"35px"}/> </Link> </li>}
                <li className="cursor-pointer"> <Link to='/books'> <PiBooks color={"black"} size={"40px"}/>  </Link></li>
            </ul>
        </nav>

    )
}

export default Navbar;