# classmate-api

https://docs.astral.sh/uv/guides/integration/docker/#caching

https://pypi.org/project/uv/#history
https://www.psycopg.org/install/
https://www.psycopg.org/psycopg3/docs/basic/usage.html
https://www.psycopg.org/psycopg3/docs/basic/install.html

https://hub.docker.com/_/postgres#how-to-use-this-image
$ docker run --name some-postgres -e POSTGRES_PASSWORD=mysecretpassword -d postgres
https://docs.djangoproject.com/en/5.2/ref/databases/#postgresql-notes

https://docs.docker.com/compose/how-tos/startup-order/

Run Project:
- docker compose -f local.yml up

docker exec -it classmate_web sh -c 'python manage.py makemigrations & python manage.py migrate'

Access db in container:
- docker exec -it classmate_db psql -U postgres -d classmate
Show db:
- \dt

Access shell in container:
- docker exec -it classmate_web python manage.py shell

Data generate in db container:
- 
- 
- docker exec -it classmate_web sh -c 'python manage.py loaddata fixture_file/3_academy_fixture.json'
- docker exec -it classmate_web sh -c 'python manage.py loaddata fixture_file/4_course_fixture.json'
- docker exec -it classmate_web sh -c 'python manage.py loaddata fixture_file/5_batch_fixture.json'
- docker exec -it classmate_web sh -c 'python manage.py loaddata fixture_file/6_grade_fixture.json'
- docker exec -it classmate_web sh -c 'python manage.py loaddata fixture_file/7_batch_enrollments_fixture.json'
-


For Mac database restore:
# database restore in docker:
- docker cp /Users/alim/Downloads/aws_classmate.sql classmate_db:/.
- docker exec -it classmate_db psql -U postgres -c "DROP SCHEMA public CASCADE;"
- docker exec -it classmate_db psql -U postgres -c "CREATE SCHEMA public;"
## restore by bellow command
- docker exec -it classmate_db sh -c "psql -U postgres -d classmate < aws_classmate.sql"
- If not work try bellow.
- docker exec -it classmate_db sh -c "pg_restore -U postgres -d classmate < aws_classmate.sql"
- To migrate
- docker exec -it classmate_web sh -c "python manage.py migrate"
- Alter docker database password if system password is different.
- docker exec -it classmate_db bash psql -U postgres du ALTER USER postgres PASSWORD '1234';

#-----------------------------------------------------
For windows database restore: (first time)
- docker cp "C:\Users\alima\Downloads\classmate.dump" classmate_db:/.
- docker exec -it classmate_db sh -c "pg_restore -U postgres -d classmate /classmate.dump"
- docker exec -it classmate_web sh -c "python manage.py migrate"
- docker exec -it classmate_db psql -U postgres -c "ALTER USER postgres PASSWORD '1234';"

For windows database restore: (Already data in database)
- docker cp "C:\Users\alima\Downloads\classmate.dump" classmate_db:/.
- docker exec -it classmate_db psql -U postgres -c "DROP SCHEMA public CASCADE;"
- docker exec -it classmate_db psql -U postgres -c "CREATE SCHEMA public;"
- docker exec -it classmate_db sh -c "pg_restore -U postgres -d classmate /classmate.dump"
- docker exec -it classmate_web sh -c "python manage.py migrate"
- docker exec -it classmate_db psql -U postgres -c "ALTER USER postgres PASSWORD '1234';"

#-----------------------------------------------------
during docker first time run update local.yml file.
  db:
    image: postgres:17
    restart: always
    container_name: classmate_db
    volumes:
      - classmate_db:/var/lib/postgresql/data/
    ports:
      - "5433:5432"
    environment:
      - POSTGRES_PASSWORD=1234
      - POSTGRES_USER=postgres
      - POSTGRES_DB=classmate
    healthcheck:
      test: ["CMD-SHELL", "PGPASSWORD=${POSTGRES_PASSWORD} pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      retries: 5
      start_period: 30s
      timeout: 10s
To make github action .scripts/deploy.sh executable run chmod +x .scripts/deploy.sh inside the server. 
-------------
upgrade django version:
pip install pip-review
pip-review --auto
-------------
pm2 stop classmate-web
or kill all: pm2 stop all
pm2 kill
restart: pm2 start classmate-web

