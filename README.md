# LLM Webapplication for candidate Cristian Vives

The following repo contains all work for a functioning web
application for Autify's technical project. The completed
project provides a web application that lets the user
generate code snippets given a natural text description. It
is written in python using python, flask, and jinja
templates for the front-end and back-end. Sqlite is used as
the database to store user, user chat data, and user
information.

## Supported models

The web application currently supports OpenAI's GPT-3.5
(turbo). I was working on getting either Llama-7B or Mixtral
in the application, but they are very big models to run on a
local GPU, and it would be tough to route many of the
existing functionality into the models given the time
constraint (such as continuing the LLM conversation, and so
on). Therefore, the next section will talk about the steps
to enable a custom LLM on this project

### Steps to allow custom LLMs to run for this project

From the ground up, this project was built with custom-LLMs
in mind, if you look at the schema for the sqlite database,
there is a specific table to hold user-models. By default
everyone gets access to gpt-3.5 but the idea was to link to
unique models that users either upload or specify from
hugging-face.

#### Considerations for running locally or on production
server

When running locally not too many considerations are needed,
since you are purely limited by your hardware and local
storage to hold the model weights. However, when running on
production it is important to understand: 1) How the models
will be executed, 2) Where the models will be stored. I will
be using AWS as our cloud infrastructure for the example.

1. Model inference - Most LLMs require a lot of VRAM, so the
   first thing would be to perhaps lower the precision of
   the model to lighten the load. We could also opt for
   serverless architecture on AWS to follow a "pay as you
   go" model, such as utilizing lambda or fargate. Lambda
   does come with some time constraints and the cold start
   can be very slow, so ECS with fargate mode enabled could
   provide the users access to faster model inference.
2. Model Storage - We could leverage S3 to store the model
   binaries as S3 storage is very cheap. If we run into any
   time constraints when reading the model data, we could
   leverage high-speed file systems such as FSx lustre which
   was designed specifically for ML workloads

#### Cost performance analysis with open source

Overall it might seem foolish to run custom models when
gpt-3.5 is so fast and cheap. However, some users might
prefer to run their own custom models that are fine-tuned
with specific data or might fear that the origin (chatGPT)
is biased.

It is also important to keep in mind that long-term API
costs could outweight the cost of renting a low-powered GPU
running an opensource model. If the user-base of the
platform increases exponentially it could be cheaper to run
local models. Currently, the cost of [gpt-3.5
turbo](https://openai.com/pricing) is $0.5 per 1M input
tokens and $1.5 per 1M output tokens. In contrast, an AWS
EC2 G5 Instance that contains a NVIDIA A10 Tensor Core GPU
with 25GB of VRAM, will cost minimum a price of $1 per hour
of use.

#### Potential scaling challenges

When using API-based LLMs the biggest scaling challenge is
API request limits, which is often tied to your premium
plan. If you integrate API-based LLMs, such as chatGPT, into
your products and they begin to get a lot of requests, it
could cost the organization a lot of money. It is important
to determine valid rate limits from within your application
and allocate higher rate limits with the LLM API when
needed. But apart from that, the scaling is not handled on
your end.

For local LLMs the story changes a lot. It is not scalable
to rent 1 GPU per user, so something that could be done in
AWS is direct model requests through a load balancer to an
Autoscaling Group running GPU instances, or a load
balancer on top of an ECS cluster, where traffic for the
same local LLM is directed to ECS instances running that
model. This is just from a networking perspective, within
pytorch itself we can leverage other techniques such as
pipeline parallelism to load large models over many devices.

## Feedback Loop for Improvement

Currently when a user generates a code snippet, the user has
the option to re-generate the output if they are not
satisfied. They can also provide feedback to the output and
have the LLM generate a new output based on the feedback,
and this feedback chain can go forever (until the number of
tokens exceed the context window)

## Prompt Security

The prompt is checked by chatGPT and it is set to be robust
against any attempts to generate non-code outputs, and will
raise an error message if the user tries to force the model
to generate any output that is not code.

## Snippet Management

For default, the user is able to view all of their generated
snippets in the homepage, and click on any of the generated
chats to get a clearer view. The user can also delete any
past chats if needed.

# How to run

It is very easy to run with Docker. Firts you will run the
following command in the same directory where the Dockerfile
is:

```
docker build -t llm_webapp .
```

Once the image is built, you can run it via

```
 docker run -p 127.0.0.1:8000:5000 llm_webapp 
```

Since flask defaults to port 5000, we decide to link it to
our local 8000 port. Navigating to `localhost:8000` will let
you log in!

# Logging in

By default no users are provided, so feel free to register
with a user and password. The registration page will allow
you supply an OpenAI key to run the API requests (not
provided with repo). Please contact me if this is an issue I
do not mind lending the API key if it is for testing a few
queries given how cheap gpt-3.5 turbo is.
