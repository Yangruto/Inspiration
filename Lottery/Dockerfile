# LABEL description="This is for creating a lottery list for MKT"
From python:3.6
WORKDIR /lottery
ADD . /lottery
RUN mkdir Download \
    && mkdir Upload \
    && pip install -r requirements.text
EXPOSE 5000
ENV FLASK_APP=create_lottery_list_web.py
CMD ["flask", "run", "--host=0.0.0.0"]