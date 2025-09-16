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


docker exec -it classmate_web sh -c 'python manage.py makemigrations & python manage.py migrate'

Access db in container:
- docker exec -it classmate_db psql -U postgres -d classmate
Show db:
- \dt

Access shell in container:
- docker exec -it classmate_web python manage.py shell


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

# 