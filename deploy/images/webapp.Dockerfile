FROM python:3.6-jessie

WORKDIR /cheeseshop

ADD . /cheeseshop

RUN ls -la /cheeseshop
RUN apt-get update && apt-get install git
RUN pip install .

EXPOSE 9980

CMD ["cheeseshop-webapp", "-p", "9980"]
