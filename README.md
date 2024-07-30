## Overview

This project is a web application designed to assist with learning for certification exams. The application presents multiple choice questions to users and tracks their progress. The questions currently in the database are sourced from dumps of the SAP CPI certification exam (this data can be changed).

## Architecture

The application is containerized using Docker and is structured with the following components:

- **Flask App**: The core application that handles the presentation of questions and the management of user progress.
- **Nginx**: Acts as a reverse proxy, routing traffic to the Flask app and enforcing HTTPS.
- **MySQL Database**: Stores the multiple choice questions and user progress.

## Features

- **Question Presentation**: Users are presented with multiple choice questions from the database.
- **Progress Tracking**: User answers are stored and updated, allowing users to track their progress over time.
- **HTTPS Enforcement**: Nginx ensures secure access to the application by enforcing HTTPS.
- **In Progress**: Use data to gather insights about question difficulty and to tailer question choices to the user

## Configuration

    Nginx: Configured to route traffic to the Flask app and enforce HTTPS.
    Domain: Domain is currently set as mcq.graydn.co.za and should be changed to the domain/IP of your server
    MySQL: The database is pre-loaded with SAP CPI certification exam questions which can be replaced with questions of your own

Contributions are welcome.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
