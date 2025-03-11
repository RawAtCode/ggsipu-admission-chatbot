import Image from 'next/image'
import React from 'react'

function Header() {
  return (
    <div className='header'>
        <div className='header-logo'>
            <Image src="/ipu-logo.png" alt="logo" width={300} height={300} />
        </div>
    </div>
  )
}

export default Header