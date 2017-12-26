# ASSET MANAGEMENT SYSTEM

If you manage a fleet of assets (like testing devices) in an organization, you might have come across the challenge of tracking their status and who is using them.
This Django application has been built with the aim of solving this issue. 

![](https://raw.githubusercontent.com/marco-lancini/asset-management/master/.github/asset_2.jpg)
![](https://raw.githubusercontent.com/marco-lancini/asset-management/master/.github/asset_3.jpg)



## Usage

1. Clone this repo

```bash
$ git clone https://github.com/marco-lancini/asset-management.git
```

2. Update the `env` file with the relevant Postgres user/password

3. Start the services with docker-compose:

```bash
$ cd assetmanagement
$ docker-compose up
```

In another terminal, setup the database schema:

```bash
$ docker-compose exec web python assetmanagement/manage.py makemigrations assets
$ docker-compose exec web python assetmanagement/manage.py sqlmigrate assets 0001
$ docker-compose exec web python assetmanagement/manage.py migrate
```

4. Create a super user

```bash
$ docker-compose exec web python assetmanagement/manage.py createsuperuser
```

5. The app can be accessed at: http://127.0.0.1/assets/ 

