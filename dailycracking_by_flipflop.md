## Crackme Notes (live analysis) [Link]([crackmes.de's dailycracking_by_flipflop by flipflop](https://crackmes.one/crackme/5ab77f5333c5d40ad448c0e0))

> Goal: find the correct password the binary expects.

---

## 1) Triage: what am I dealing with?

First thing I do on any unknown sample:

``` 
file ./sample
```
This confirmed it’s a Windows executable (PE) and the rest of the work makes sense in a 32-bit/x86 + MSVCRT kind of world.

Next, I immediately dump strings:

``` 
strings ./sample > file.txt
```

Interesting strings I found early:

```
Crackit 
pass: 
LIBGCCW32-EH-2-SJLJ-GTHR-MINGW32
```

At this point I did the obvious “maybe it’s that simple?” test: I tried the long MinGW runtime string as the password just to see if it’s a joke crackme. It wasn’t.

So I moved on.

---

## 2) Strings pivot: what functions suggest the logic?

Continuing through `strings`, I saw:

- `strcmp`
- `strncpy`

That was the first real “signal.” If a crackme includes `strcmp`, something is comparing my input to _something_. If `strncpy` is present, maybe the “something” is being _built_ in a buffer before comparing.

I didn’t know yet whether the expected password was:

- Hardcoded in `.rdata`, or
- Constructed at runtime (stack/register manipulation)

So I opened the binary in Ghidra.

---

## 3) Ghidra: follow main() first

In `main`, the flow was basically:

1. Print a prompt (`"pass: "`).
2. Read input via `fgets` (small length, looked like 8).
3. Call `isOk(user_input)`.
4. If `isOk` returns 0 → print failure message.
5. Else → print success message.

The branching was done with:

text

```
TEST EAX, EAX 
JZ   failure
```

I initially wondered: “Is it comparing my password with some value in EAX?”  
But after tracing, it clicked: `EAX` is just the return value from `isOk()`. The `TEST EAX, EAX` is the common “is return value zero?” check (sets flags based on whether EAX is 0).

So the _real_ work is inside `isOk()`.

---

## 4) isOk(): the real password logic

Inside `isOk`, I saw what I expected:

- A buffer gets prepared.
- `strncpy` is called with `"Crackit"`.
- Then `strcmp` compares something with my input.

At this point I was thinking:

> “Okay, so password is probably `Crackit`.”

But then I noticed something weird: it calls `getDay()` with **buffer+5**.

That’s not normal if you’re just comparing to `"Crackit"`.

## What isOk() is doing (reconstructed)

This is what it effectively does:


``` c
char buf[8];                 // stack buffer 
strncpy (buf, "Crackit", 8);         // copy base string 
getDay(buf + 5);             // overwrite starting at index 5 return 
strcmp(user_input, buf) == 0;
```

So the password is **not** just `"Crackit"`— it’s `"Crack"` + something dynamic.

That “something dynamic” is why my early guesses failed.

---

## 5) getDay(): my wrong assumption (and fix)

When I first saw `getDay()`, I saw `strftime` and I jumped to the idea:

> “It probably writes the weekday like Wed/Thu… so password might be `CrackWed`.”

That sounded plausible, but it didn’t work. And honestly it didn’t even occur to me to check the format constant at first—I assumed.

## The key lesson: don’t guess constants—inspect them

I finally looked at the referenced data in Ghidra:

``` text

... MOV ..., DAT_00403013

And the `DAT_00403013` bytes were:


25 64 00 ...

That’s "%d\0" — not "%a".
```

So `strftime` is formatting **day-of-month** (01–31), not day name.

For `strftime`, `%d` is the day of month as a zero-padded decimal number (e.g., `07`).​

So now `getDay(buf+5)` makes perfect sense:

- `"Crackit"` is 7 chars + null

- Starting at index 5 (0-based), we overwrite:
    - index 5 and 6 with two digits (like `0` and `7`)
    - and then a null terminator

Meaning:

- `"Crackit"` becomes `"Crack07"` on the 7th day of the month

---

## 6) Final password (for Jan 7)

Given the current date in the environment is January 7, the day-of-month is `07`, and `%d` yields `"07"`.​

So the password is:
`Crack07`

---

## 7) What tripped me up

- I saw `strftime` and assumed `%a` (weekday abbreviation) without verifying the actual data constant.
- Since I’m new to RE, I didn’t instinctively pivot to inspecting `DAT_...` immediately.
- Once I checked `DAT_00403013` and saw `"%d"`, the rest fell into place instantly.

Also: I found a writeup where the author wrote a small C++ program to compute the password after reversing. My methodology matched most of the way, but instead of coding, I stayed in Ghidra until I extracted the final missing detail (the format string in `.rdata`).

---

## Appendix: tiny checklist I’ll follow next time

- [ ] Always inspect referenced `DAT_...` / `.rdata` strings when I see formatting functions.
- [ ] When I see `TEST reg, reg` + conditional jump, treat it as “check return value,” not a comparison between two values.
- [ ] If `strcmp` is in play, hunt for **string construction** routines (`strncpy`, `sprintf`, `strftime`, etc.) before assuming the expected string is static.
