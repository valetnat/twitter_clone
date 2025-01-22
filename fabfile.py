from fabric import task, Connection
import os


@task
def deploy(ctx):
    with Connection(
        host=os.environ["MY_HOST"],  # host of your server
        user=os.environ["MY_USER_NAME"],
        connect_kwargs={"key_filename": os.environ["SERVER_SSH_PRIVET_KEY"]},  # ssh privet key
    ) as c:
        with c.cd("/home/ec2-user/automated-deployment"):  # use path to application
            c.run("docker-compose down")
            c.run("git pull origin master --rebase")
            c.run("docker-compose up --build -d")
