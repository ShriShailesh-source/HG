from pycaw.pycaw import AudioUtilities
import time

def test():
    dev = AudioUtilities.GetSpeakers()
    ev = dev.EndpointVolume
    print('Current scalar:', ev.GetMasterVolumeLevelScalar())
    print('Setting to 0.3')
    ev.SetMasterVolumeLevelScalar(0.3, None)
    time.sleep(0.5)
    print('After set scalar:', ev.GetMasterVolumeLevelScalar())
    print('Setting to 0.7')
    ev.SetMasterVolumeLevelScalar(0.7, None)
    time.sleep(0.5)
    print('After set scalar:', ev.GetMasterVolumeLevelScalar())

if __name__ == '__main__':
    test()
