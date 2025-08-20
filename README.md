# STservo Driver

* Waveshare sells SC-series and ST-series servos and their wired and wireless drivers.
* I found its [official python SDK](./misc/SCServo_Python.zip) is a piece of sh*t so I write this version of driver for myself and the learner.
* Keeping thing in one place and in a minimalist style shows your good faith for other devs!

<table>
    <tr>
        <td>
            <a href='https://www.waveshare.net/wiki/SC09_Servo'>SC09</a>
        </td>
        <td>
            <a href='https://www.waveshare.net/wiki/ST3215_Servo'>ST3215</a>
        </td>
    </tr>
    <tr>
        <td><img src='./misc/Servo_SC09.jpg'   height="100"></img></td>
        <td><img src='./misc/Servo_ST3215.jpg' height="100"></img></td>
    </tr>
    <tr>
        <td><a href='https://www.waveshare.net/wiki/Bus_Servo_Adapter_(A)'>Bus Servo Adapter (A)</a></td>
        <td><a href='https://www.waveshare.net/wiki/Servo_Driver_with_ESP32'>Servo Driver with ESP32</a></td>
    </tr>
    <tr>
        <td><img src='./misc/Adapter_A.jpg'   height="100"></img></td>
        <td><img src='./misc/Driver_with_ESP32.jpg' height="100"></img></td>
    </tr>
</table>

## Bus Servo Adapter (A) Spec

* 输入电压 input voltage：< 12.6V（输入电压需要与舵机电压匹配 the voltage supplied to the driver board may be in the voltage range of the servo.）
* 通信接口 comm protocol：UART
* 供电接口 power jack：5.5*2.1mm DC
* 产品尺寸 measurement：42mm x 33mm
* 固定孔通径 diameter of mounting hole：2.5mm 
* 适用舵机 compatible servo：多达up to 253个ST/SC系列总线舵机

## 接线方式

* UART: <b style='color:red'>Tx-Tx, Rx-Rx</b>
* USB

## ~~SDK~~

* ~~Waveshare provides two python SDKs [STServo_Python.zip](https://www.waveshare.net/wiki/%E6%96%87%E4%BB%B6:STServo_Python.zip) and [SCServo_Python.zip](https://www.waveshare.net/wiki/%E6%96%87%E4%BB%B6:SCServo_Python.zip), but only SCServo_Python is needed.~~

### Usage
