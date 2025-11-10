# Guidelines for creating test data

<!-- TOC -->
* [Guidelines for creating test data](#guidelines-for-creating-test-data)
    * [Terminology](#terminology)
    * [Multiple apps](#multiple-apps)
  * [1. Plan ahead](#1-plan-ahead)
    * [Investigate the application](#investigate-the-application)
    * [Create a script](#create-a-script)
    * [Consider using self-descriptive data](#consider-using-self-descriptive-data)
    * [Generating large amounts of realistic data](#generating-large-amounts-of-realistic-data)
  * [2. Creating the test data](#2-creating-the-test-data)
    * [Creating test data with Puma](#creating-test-data-with-puma)
    * [Creating test data manually](#creating-test-data-manually)
  * [3. Extracting and storing the test data](#3-extracting-and-storing-the-test-data)
    * [Extraction](#extraction)
    * [Storing the test data](#storing-the-test-data)
  * [4. Conclusion](#4-conclusion)
<!-- TOC -->

At the NFI, we have been making reference data for some time now, and through the years we discovered some best
practices improving our process, but also the quality of the data itself. If you are also using Puma to create
reference or test data, this document will help you to create your datasets better and faster. But even if you don't use
Puma, this document will help you in the process of creating test data.

If you are wondering whether you should create your own test data over just using publicly available data, or if you are
deciding whether to use Puma over manually creating test data, [this document](TESTDATA_WHY.md) goes into the advantages
of creating the data yourself, and automating the process.

### Terminology

In this document, the terms test data and reference data are used interchangeably. While they aren't exactly the same
thing, the difference is in the use of the data, not the contents of it. Since this document is only about how we create
this data, in this document the terms can be considered synonymous.

### Multiple apps

In this document we often talk about 'your application', and the assumption seems to be made that only one application
is involved in the creation of your test data. Of course, this isn't necessarily the case: You might want to create
reference data involving multiple applications.

If this is the case, this document still applies: anywhere we mention 'your application' consider this as 'your one or
more applications'. Puma is perfectly able to operate multiple apps at the same time, and all principles considered in
this document apply to multiple applications just as well as they do to one.


## 1. Plan ahead

The first step is careful planning. You might be tempted to just start sending messages or start browsing in the app
you want to generate reference data for, but from experience we learned creating test data is something best properly
planned ahead.

### Investigate the application

As [stated before](#Completeness), apps these days have MANY features. Therefore, it's a good idea to explore the
application you want to create test data with. Even if you frequently use this app privately, you'll probably find
features you never knew existed.

If you're creating the reference data for a specific goal (forensic research, network analysis, or something else),
keep this goal in mind: if you're only doing forensic research on pictures, there's probably no need to delve into the
details of calendar appointments... Although: make sure to check if those appointments can contain a picture or
thumbnail!

The goal of this investigation is having a concise list of application features you want to cover.

### Create a script

When you have a list of all features you want to cover, it's time to write a script. And this isn't necessarily a Puma
script: Puma can help you to automate actions, but if your reference data is about an app that Puma doesn't support, and
you're just going to cover 10 user actions, you'll probably save time by executing the actions manually to create your
reference data.

Still, even when you create the data manually, write down a **precise**, **chronological** and **complete** description
of all actions you will take to create the reference data.

By **precise** we mean there should be no room for ambiguity. `send a picture in whatsapp` is not precise: does this
mean using the embedded camera to take a picture and send it, or does it mean sending a picture stored on the device?
Be sure every action in your script unambiguously describes one specific user action in the application.

By **complete** we mean you should obviously include all actions you will take, but also actions you will not take:
after sending a picture from user 1 to user 2, include in your script whether Bob opens the picture. When making a call
from user 1 to user 2, and user 2 should answer, include how long user 2 should wait before answering.

By **chronological** we mean that you should write the actions in the order you want to execute them (obviously).

If you use Puma, your script will look something like this:

```python
alice = WhatsappActions('emulator-5554')
bob = WhatsappActions('emulator-5556')
alice.send_message(f'1. This is the first message, sent by Alice to Bob, sent at {current_time()}', chat='Bob')
sleep(60)
bob.send_message(f'2. This message is sent by Bob to Alice, sent at {current_time()}', chat='Alice')
```

If you create the test data manually, your script won't be Python code but will look similar:

```
Alice to Bob at hh:mm: 1. This is the first message, sent by Alice to Bob, sent at hh:mm
(wait 1 minute)
Bob to Alice at hh:mm: 2. This message is sent by Bob to Alice, sent at hh:mm
```

You will notice we are waiting a full minute between the messages. We often do this (not between all messages, but
between some) because we will use our reference data to analyze the file format. By waiting a full minute there is a
distinct difference between the timestamps, making it easier for se to keep these timestamps apart and verify them.

You can also see we're prepending the messages with a sequence number. We do this because it makes it easier for us to
verify whether we could retrieve all sent messages form the reference data, and whether the order of messages is
maintained in storage.

Lastly, you'll notice the messages aren't a simple `Hi!`. This is what we call self-descriptive data and for our
research at the NFI we vastly prefer this over realistic messages.

### Consider using self-descriptive data

Depending on the goal of your reference data, you might want to consider using self-descriptive data. This is data of
which the content describes itself, for example a chat message `This is a message from Alice to Bob sent at 2024-10-01
14:53 UTC`, or a layer in a layered image file containing `This is text on layer 1, the letters are red, and there is
a second layer with blue text`.

Self-descriptive data comes in very handy when you're doing (forensic) analysis of a file format, as it makes it easier
to interpret the data and prevent mistakes.

### Generating large amounts of realistic data

If the goal of your reference data is not to analyze the data content itself, but rather to create a large amount of
very realistic synthetic data, obviously self-descriptive data is not for you.

If you want to create large amounts of realistic user data (like thousands of chat messages that look real), have an
LLM make up the conversations, and use Puma to send these messages in realistic intervals. How to do that is beyond the
scope of this document, but current day LLMs are smart enough to understand the Puma API (just give it the Python code
and the LLM will understand) and ask it to generate the Python code containing the number of messages you need, on
topics you want.

## 2. Creating the test data

> ⚠️ If your goal is to capture network traffic, don't forget to start recording network traffic when you start
> generating traffic. We've been there.

### Creating test data with Puma

If your app is not supported in Puma, you will need to add support for it. To do so, read
the [contributing documentation](../CONTRIBUTING.md).

After you have written the Puma code and your Puma script, you can now execute it. Be sure to properly prepare the
device ([enable USB debugging!](../README.md#adb-device-cannot-connect)) and install the application. It's a good idea to
go into the app settings and grant all possible permissions to the app, to prevent popups from getting in the way of
your Puma script.

If this is the first time you're running your script, we recommend 'babysitting' it: it is very possible that some
actions will fail, and when you see what happens it'll be easier to fix your code. Sometimes you can also manually
intervene and do a tap that you forgot to put in your Puma code.

If you are repeating this experiment, after babysitting your Puma script once or twice all the problems should be ironed
out and a complete hands-off approach should be possible: just start the script and go get some coffee!

### Creating test data manually

We highly recommend to manually create test data with two people: an operator who operates the device(s), and a
coordinator who handles the script. The coordinator tells the operator which action to take next, and annotates the
script with the timestamps. In case the operator makes a mistake (makes a typo or executes the wrong user action in
the UI, or perhaps the coordinator gave the wrong instruction), the coordinator also writes this down.

At first glance it might seem overkill to have two people 'just play around with a phone', but a mistake is made very
easily. Having two people in this process greatly reduces the number of mistakes you will make (yes, mistakes will be
made).

By having the coordinator annotate everything, you end up with a complete and correct script of all actions that were
taken, including the timestamps. This is valuable metadata that you can store along your reference data after
extraction, so when you analyze the reference data, you know exactly how it was created and what you can find in that
data.

## 3. Extracting and storing the test data

### Extraction

After you have executed the script, your reference data is now ready, you just need to extract it. How to do this
depends on what data you need:

1. If you do network analysis, I hope you didn't forget to record the network traffic!
2. If you want a full device image, use your favorite tool to make this image
3. If you only want specific app data, you'll need to delve into the device to find its location

If you're handling one of the first two cases, you probably know which tool you need for the job.

In the last case, you might not know where to get the data. The location of app data is dependent on the OS and the
app itself.

Luckily on modern mobile devices, apps cannot just store data anywhere they want. On Android, relevant app data is
usually stored in `/data/data/<package name of your app>`, with protected media files sometimes being stored in
`/data/media/Android/data/<package name of your app>`. Within this folder, the app can choose how to store its data.
What we usually do is copy this entire folder and then explore this data.

### Storing the test data

After you extracted the data you want, you can now do your thing with it, but after that, you probably don't want to
delete it.

At the NFI, we store all reference data, along with metadata describing the reference data. This metadata file includes
the following:

* File type + version if applicable
* Creation date + location
* Device + OS on which it was created
* Content description (eg `chat database of foo@bar.com, containing 213 messages`)
* Reproduction steps: the exact and complete steps you took to create this data. This contains either a reference to
  your Puma script, or the annotated script

By storing these together, you can start building a full archive of high-quality reference data of which anyone can
easily find out where data came from and how it was created. If anyone in the (far) future ever wants to reproduce your
process, or expand on it, they can now easily do so.

## 4. Conclusion

The creation of test data is not a trivial thing, and doing it right even less so. This document tries to summarize the
most important best practices. Some of them might sound trivial, but we can assure you we only thought of them after
doing things differently first, resulting in either wasted time or test data of lower quality.

This document of course is far from the last thing to be said on the topic, and I'm sure we'll make changes to it in the
future.
