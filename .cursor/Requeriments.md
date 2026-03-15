# Renfe Tracker

Renfe is a company in Spain that operate trains, they have a website that allow users to buy tickets. They have different services, but for this project we are only interested in what we cal "media o larga distancia", which means. They have many trains, like AVE, Alvia, Inter-city, Regional Express, Tren Hotel and more. 

# Purpose of the project
The purpose of the project is to track, learn, and suggest possible trains and their possible prices for the given dates by a user. This will be better explained in this document. 

# Original Renfe Website
The original website is https://www.renfe.com/es/es and it allows users to search for the following:
- Dates for a trip
- Dates can be one way or 2 ways
- Source location
- Destination location
- Number of people (including kids or not)

The website might show some discounts and other stuff related to special cases, like young people, old people and so on, but we are not interested on any of this discounts. We are going to assume that we don't care at all about discounts like this. 

This website might require to keep cookies or session to search properly.

# Aplication to be built

## Built for Docker self-hosted
First of all, this application is going to be served with docker and it is designed to be self-hosted by anyone using it. This is not a web service that anyone will be using in the world, so each person that wants to use this application will need to run the docker or docker compose on their own. This has some implications, like we need to provide a docker with everything inside, using proper volumes and ports, and that we don't care about high availability or many concurrent users or many processes running at the same time or a big database being used. 

## Web interface
We want to build a website, that as described, will run locally, that is as close as possible to the original Renfe website. It means that we'll need to pick the design, css, styles, and so on, so it looks very similar. We'll add some new features on our applications. 

## Database
As this is going to run in docker and be self-hosted, we don't need a huge database, so, ideally, we'll use something like sqllite or similar, or we can consider using something that works better for our use case

## Programming language
We don't have strong opinions about the language, so we leverage the decision on the languages to the architect, backend and frontend developers. They need to find whatever is the best for this use case.

## Scheduler
As described in features, we'll need to run periodically some queries to the original Renfe website to detect some changes, so there is a need to schedule some actions. I don't know what's the best for this, so the developers and architect need to use or design a simple but good mechanism to schedule tasks. 

## Features

### Initical interface
The initial website will show a website, similar to the original Renfe website in colors and styles, but with basic information, like in a table, about:
- Your tracked trips

There will be a button to "Track new trip". When "track new trip" is clicked, the applications goes to the next step, which is the search for trips.

### Interface for search trips
The user accessing to our renfe-tracker will see a website very very similar to the original Renfe website. We don't need all the non-relevant content from the original, so if there are links, ads, messages, news, or any other content like that, we don't need to show anything similar. 
We need to show the same form input the original website is showing, but with small changes to make it easier for our application.

 The form needs to include the following:

- Date to be selected
- Source location (ideally, it should show the same possible locations to chose, but we can start with a smaller list if needed)
- Destination location (same on destination, we should show all possible locations, but we can start with a smaller list if that makes everything easier)
- We assume only 1 adult is traveling.

Differences with the original website:
- We don't show "ida y vuelta" dates, so only one date is selected, we only care about one way trips. 
- We don't show how many people travel, we assume only one person will travel. 

After the inputs, the user can click "search" or similar, and it goes to the results.

### Showing results

The results will be very similar to the results showed by the original Renfe website when a search is being made, this is, showing the available trains and their prices. This usually shows also which train it is (like Ave, Alvia, Intercity, etc) and the duration of the travel. 

Our Renfe-tracker will show extra information in this page:
- The trains will show the price, but they will also show and estimated price range. For example, if the original price today is 60€, the application will show that prices are usually from 30€ ~ 70€. Later the rules to detect this prices are explained. 
- Possible trains that doesn't appear in the original website, but are expected to appear soon.
  - On these trains, the color of the card will be slightly different, and they will have an icon or similar that shows they are "possible train not published yet". 
  - For these possible trains, the price will behave like the normal trains, it will show the possible ranges.
  - For these possible trains, we'll show also when it is estimated that they will be publicly available. (More details about how to know this later) 

### Estimating trains a prices

Estimating trains a prices in Renfe is easy, they follow simple rules:
- Looking a lot of time ahead, Renfe doesn't show all the trains, but they are standard and defined for each week day. So, if you look for a Friday next month, it will show some trains, but if you look for the next Friday, the closest one, it will show you all trains availables on Fridays, so you can know that on a Friday in 1 or 2 months, those trains will be available. 
- To understand when a train becomes available, the application needs to go to the official website and check the same weekday for the next weeks, and it will understand how many weeks ahead a train is published. 
- To understand the posible price of a train, the application can check the same train in different days, and see how much it costs. Usually, trains far from now are more expensive than closer trains. Weekday might affect the price, but not much. For example, a train on a Thursday at 5pm might cost 120€ if it is in 5 week from now, but next Thursday it might cost only 30€. The same train might exists also in other week days, fo maybe on a Monday at 5pm costs only 25€. These prices are interested and counted to the "possible price". But if the train is in a different time, they are not related and we cannot assume their prices are related. 

Because all this information that is obtained doing queries to the original website are very interesting, they application will save them in a database for future comparisons. 

### Tracking a trip 

The previous feature about showing possible prices is very great on its own, but we want to do more. We want to track the prices for a specific train and save them in a database when the price changes, so we'll know the times when prices change.

To track a trip, the user needs to pick a train, which can be a real Train or a "possible train not published yet", and the application will ask the user how ofter do they want to track the train. It will suggest every 1h as prices doesn't change that often, but the user can introduce the number of hours desired. 
Then, the application will save this trip in the database, it will appear in the initial page, and it will run a query to the original website using the defined schedule, to find the real price. If the real price drops or goes up, it will detect it. When it detects this, it will save it to the database, related to this trip tracked. 

### Seeing tracked trains
If the user, in the initial page, clicks on a tracked trip, the application will show the events that it has detected. Events are price changes. So if the application know that prices changed a few times, it will show a row for each price change, and the date when it was detected. 
