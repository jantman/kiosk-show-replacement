# UI Fixes - High Priority

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

This document tracks high priority UI issues with significant functionality impact. For each of these issues, unless stated otherwise, we must FIRST write an integration test that checks for the desired behavior (should initially be failing), then implement our fix and verify that the test now passes.

## Issues

---

### 1. New Default Slideshow

**Location:** Slideshow create page

**Description:** When I create a new slideshow and check the `Set as Default Slideshow` box, this is not persisted.

**Expected:** The default slideshow checkbox should be saved when creating a new slideshow.

**Status:** Open

---

### 2. Text Title

**Location:** Display view page (slideshow playback)

**Description:** Text slides are displaying the title in addition to the text; they should only display the "Text Content".

**Expected:** Text slides should only show the text content, not the title.

**Status:** Open
