 CREATE DATABASE IF NOT EXISTS matcha;
 

  CREATE TABLE  IF NOT EXISTS accounts(
        id INT(11) NOT NULL PRIMARY KEY AUTO_INCREMENT,
        username VARCHAR(250) NOT NULL UNIQUE,
        firstname VARCHAR(250) NOT NULL UNIQUE,
        lastname VARCHAR(250) NOT NULL UNIQUE,
        password VARCHAR(250) NOT NULL,
        email VARCHAR(250) NOT NULL UNIQUE,
        vkey VARCHAR(250) NOT NULL,
        user_email_status enum('not verified','verified') NOT NULL,
        picture VARCHAR(500) NOT NULL DEFAULT profile.jpg
    );

    
  CREATE TABLE IF NOT EXISTS profiles(
        id INT(11) NOT NULL PRIMARY KEY AUTO_INCREMENT,
        user_id INT(11) NOT NULL UNIQUE,
        gender VARCHAR(250) NOT NULL UNIQUE,
        sexual_orientation VARCHAR(250) NOT NULL UNIQUE,
        bio VARCHAR(250) NOT NULL UNIQUE,
        listofinterest VARCHAR(250) NOT NULL UNIQUE,
        FOREIGN KEY(user_id) REFERENCES accounts(id)
    );


   CREATE TABLE IF NOT EXISTS images(
        id INT(11) NOT NULL PRIMARY KEY AUTO_INCREMENT,
        user_id INT(11) NOT NULL,
        image_path VARCHAR(500) NOT NULL,
        FOREIGN KEY(user_id) REFERENCES accounts(id)
    );

